from flask import Flask, render_template, request, redirect, url_for
import pymysql
from dotenv import load_dotenv
import os
import boto3
from werkzeug.utils import secure_filename
import uuid

load_dotenv('private/.env')

app = Flask(__name__, template_folder='public/templates', static_folder='public/static')

db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'charset': 'utf8mb4'
}

S3_BUCKET = os.environ.get('S3_BUCKET')
S3_REGION = os.environ.get('S3_REGION')

def get_db():
    return pymysql.connect(**db_config)

def get_s3():
    return boto3.client('s3', region_name=S3_REGION)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            image_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_url = None

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{ext}"
                s3 = get_s3()
                s3.upload_fileobj(
                    file,
                    S3_BUCKET,
                    filename,
                    ExtraArgs={'ContentType': file.content_type}
                )
                image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO posts (title, content, image_url) VALUES (%s, %s, %s)',
            (title, content, image_url)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('new_post.html')

@app.route('/post/<int:id>')
def post_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = %s', (id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('post_detail.html', post=post)

@app.route('/post/<int:id>/delete', methods=['POST'])
def delete_post(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT image_url FROM posts WHERE id = %s', (id,))
    post = cursor.fetchone()
    if post and post[0]:
        filename = post[0].split('/')[-1]
        s3 = get_s3()
        s3.delete_object(Bucket=S3_BUCKET, Key=filename)
    cursor.execute('DELETE FROM posts WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80, debug=True)