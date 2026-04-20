from dataclasses import dataclass
import pymysql.cursors

@dataclass
class Post:
    title: str
    content: str
    image_url: str
    cognito_sub: str

# postsの初期化
def init_posts_table(conn):
    with conn.cursor() as cursor:
        sql = '''
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            image_url VARCHAR(255),
            cognito_sub VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''
        cursor.execute(sql)
        conn.commit()

# 投稿一覧の取得
def get_all_posts(conn):
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = '''SELECT p.*, u.display_name, u.profile_image_url AS user_image 
                 FROM posts p
                 LEFT JOIN users u ON p.cognito_sub = u.cognito_sub
                 ORDER BY p.created_at DESC'''
        cursor.execute(sql)
        return cursor.fetchall()

# 投稿の追加
def add_post(conn, post: Post):
    """
    引数をPostクラスに限定することで、データの入れ忘れを防ぎます
    """
    with conn.cursor() as cursor:
        sql = '''INSERT INTO posts (title, content, image_url, cognito_sub) 
                 VALUES (%s, %s, %s, %s)'''
        cursor.execute(sql, (
            post.title,
            post.content,
            post.image_url,
            post.cognito_sub
        ))
        conn.commit()

# 投稿の詳細の取得
def get_post_by_id(conn, post_id):
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = '''SELECT p.*, u.display_name, u.profile_image_url AS user_image 
                 FROM posts p
                 LEFT JOIN users u ON p.cognito_sub = u.cognito_sub
                 WHERE p.id = %s'''
        cursor.execute(sql, (post_id,))
        return cursor.fetchone()

# 投稿の削除
def delete_post_by_id(conn, post_id):
    with conn.cursor() as cursor:
        sql = 'DELETE FROM posts WHERE id = %s'
        cursor.execute(sql, (post_id,))
        conn.commit()

# 画像URLの取得
def get_image_url(conn, post_id):
    with conn.cursor() as cursor:
        sql = 'SELECT image_url FROM posts WHERE id = %s'
        cursor.execute(sql, (post_id,))
        result = cursor.fetchone()
        return result[0] if result else None