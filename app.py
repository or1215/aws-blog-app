from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql.cursors
from dotenv import load_dotenv
import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid
import hmac
import hashlib
import base64

# ---- DB操作のモジュールをインポート ----
# blogの投稿に関する情報
from db.posts import init_posts_table, Post, add_post, get_all_posts, get_post_by_id, delete_post_by_id, get_image_url
# ユーザーに関する情報
from db.users import init_users_table, User, add_user, get_user_by_cognito_sub, update_user

load_dotenv('private/.env')

# Flaskアプリの設定
app = Flask(__name__, template_folder='public/templates', static_folder='public/static')
app.secret_key = os.urandom(24)

# DB接続設定
db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'charset': 'utf8mb4'
}

# AWS S3の設定
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_REGION = os.environ.get('S3_REGION')

# AWS CloudFrontのドメイン
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN')

# Cognito（ログイン）の設定
COGNITO_REGION = os.environ.get('COGNITO_REGION')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

# DB接続
def get_db():
    return pymysql.connect(**db_config)

# AWS S3クライアントの取得
def get_s3():
    return boto3.client('s3', region_name=S3_REGION)

# AWS Cognitoクライアントの取得
def get_cognito():
    return boto3.client('cognito-idp', region_name=COGNITO_REGION)

# DB初期化
def init_db():
    conn = get_db()
    try:
        init_posts_table(conn)
    finally:
        conn.close()

# ログイン必須のデコレーター
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- ルーティング設定 ---
# トップページ（投稿一覧）
@app.route('/')
def index():
    conn = get_db()
    try:
        posts = get_all_posts(conn)
        return render_template('index.html', posts=posts)
    finally:
        conn.close() 

# 新規投稿　ログイン必須
@app.route('/post/new', methods=['GET', 'POST'])
@login_required 
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_url = None
        cognito_sub = session['cognito_sub']

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
                image_url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"

        conn = get_db()
        try:
            post = Post(title=title, content=content, image_url=image_url, cognito_sub=cognito_sub)
            add_post(conn, post)
            return redirect(url_for('index'))
        finally:
            conn.close() 
    return render_template('new_post.html')

# 投稿詳細
@app.route('/post/<int:id>')
def post_detail(id):
    conn = get_db()
    try:
        post = get_post_by_id(conn, id)
        if not post:
            flash('投稿が見つかりませんでした。', 'error')
            return redirect(url_for('index'))
        return render_template('post_detail.html', post=post)
    finally:
        conn.close()

# 投稿削除 ログイン必須
@app.route('/post/<int:id>/delete', methods=['POST'])
@login_required 
def delete_post(id):
    conn = get_db()
    try:
        # s3から画像の削除
        image_url = get_image_url(conn, id)
        if image_url:
            # ファイル名を抽出
            filename = image_url.split('/')[-1]
            try:
                s3 = get_s3()
                s3.delete_object(Bucket=S3_BUCKET, Key=filename)
            except Exception as e:
                print(f"S3削除エラー: {e}")
        # DBから投稿データを削除
        delete_post_by_id(conn, id)
    finally:
        conn.close() 
    return redirect(url_for('index'))

# プロフィール編集　ログイン必須
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        new_display_name = request.form.get('display_name')
        new_bio = request.form.get('bio')
        cognito_sub = session['user_info']['cognito_sub']
        profile_image_url = session['user_info'].get('profile_image_url')
        if 'avatar' in request.files:
            file = request.files['avatar']
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
                profile_image_url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"
        conn = get_db()
        try:
            # DBのuser情報を更新
            user = User(
                display_name=new_display_name,
                bio=new_bio,
                cognito_sub=cognito_sub,
                profile_image_url=profile_image_url  # 画像URLは変更なし
            )
            update_user(conn, user)
            # 更新後のユーザー情報をDBから取得
            updated_user = get_user_by_cognito_sub(conn, cognito_sub)
            if updated_user:
                # datetime型を文字列に変換
                if updated_user.get('created_at'):
                    updated_user['created_at'] = updated_user['created_at'].isoformat()
                # セッション情報を最新に上書き
                session['user_info'] = updated_user
                session['user'] = updated_user['display_name']
            flash('プロフィールを更新しました。', 'success')
            return render_template('edit_profile.html', user=session['user_info'])
        except Exception as e:
            print(f"Update Error: {e}")
            flash('更新に失敗しました。', 'error')
        finally:
            conn.close()
    return render_template('edit_profile.html', user=session['user_info'])

# ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        display_name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # バリデーション（フロント側チェック）
        if len(password) < 8:
            flash('パスワードは8文字以上で入力してください。', 'error')
            return render_template('register.html')
        if not display_name:
            flash('ユーザー名を入力してください。', 'error')
            return render_template('register.html')
        try:
            cognito = get_cognito()
            username = str(uuid.uuid4())  # ユニークなIDを生成
            cognito.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                SecretHash=get_secret_hash(username),  # usernameで計算
                Username=username,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'nickname', 'Value': display_name}
                ]
            )
            flash('登録確認メールを送信しました。メールを確認してください。', 'success')
            # usernameをセッションに保存（confirm時に必要）
            session['reg_username'] = username
            session['reg_email'] = email
            return redirect(url_for('confirm'))
        except ClientError as e:
            # CognitoのエラーコードをJapanese化
            error_code = e.response['Error']['Code']
            error_messages = {
                'UsernameExistsException'    : 'このメールアドレスはすでに登録されています。',
                'InvalidPasswordException'   : 'パスワードは8文字以上で、大文字・小文字・数字・記号を含めてください。',
                'InvalidParameterException'  : '入力内容に誤りがあります。メールアドレスの形式を確認してください。',
                'TooManyRequestsException'   : 'しばらく時間をおいてから再度お試しください。',
                'CodeDeliveryFailureException': 'メールの送信に失敗しました。メールアドレスを確認してください。',
            }
            message = error_messages.get(error_code, 'エラーが発生しました。もう一度お試しください。')
            flash(message, 'error')
    return render_template('register.html')

# メール認証
@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    email = session.get('reg_email', '')
    username = session.get('reg_username', '')
    if request.method == 'POST':
        code = request.form['code']
        try:
            cognito = get_cognito()
            cognito.confirm_sign_up(
                ClientId=COGNITO_CLIENT_ID,
                SecretHash=get_secret_hash(username),  # usernameで計算
                Username=username,
                ConfirmationCode=code
            )
            flash('メール認証が完了しました。ログインしてください。', 'success')
            session.pop('reg_username', None)
            session.pop('reg_email', None)
            return redirect(url_for('login'))
        except ClientError as e:
            flash(e.response['Error']['Message'], 'error')
    return render_template('confirm.html', email=email)

# ログイン処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            cognito = get_cognito()
            response = cognito.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password,
                    'SECRET_HASH': get_secret_hash(email)
                }
            )
            # 認証成功後のアクセストークンを取得
            access_token = response['AuthenticationResult']['AccessToken']
            # ユーザー情報の取得
            user_info = cognito.get_user(AccessToken=access_token)
            cognito_sub = None
            display_name = "ゲスト"
            for attr in user_info.get('UserAttributes', []):
                if attr['Name'] == 'sub':
                    cognito_sub = attr['Value']
                elif attr['Name'] == 'nickname':
                    display_name = attr['Value']

            # userを確認・登録
            conn = get_db()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    user_in_db = get_user_by_cognito_sub(conn, cognito_sub)
                    if not user_in_db:
                        try:
                            new_user = User(
                                display_name=display_name,
                                bio='',
                                cognito_sub=cognito_sub,
                                profile_image_url=''
                            )
                            add_user(conn, new_user)
                            user_in_db = get_user_by_cognito_sub(conn, cognito_sub)
                        except Exception as e:
                            print(f"ユーザー登録エラー: {e}")
                            flash('ユーザー情報の保存に失敗しました。', 'error')
                # ユーザー情報をまるごとセッションに保存（RDSを見に行かなくて済むように）
                if user_in_db.get('created_at'):
                    user_in_db['created_at'] = user_in_db['created_at'].isoformat()
                session['user_info'] = user_in_db
            finally:
                conn.close()
            
            session['user'] = display_name
            session['token'] = access_token
            session['cognito_sub'] = cognito_sub
            flash('ログインしました。', 'success')
            return redirect(url_for('index'))
        except ClientError as e:
            flash(e.response['Error']['Message'], 'error')
    return render_template('login.html')

# ログアウト処理
@app.route('/logout')
def logout():
    session.clear()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('index'))

# Cognitoのシークレットハッシュを生成する関数
def get_secret_hash(username):
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

# アプリの起動
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80, debug=True)