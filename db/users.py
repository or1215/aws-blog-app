from dataclasses import dataclass
import pymysql.cursors

@dataclass
class User:
    display_name: str
    bio: str
    cognito_sub: str
    profile_image_url: str

# usersの初期化
def init_users_table(conn):
    with conn.cursor() as cursor:
        sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            display_name VARCHAR(255) NOT NULL,
            bio TEXT,
            cognito_sub VARCHAR(255) NOT NULL UNIQUE,
            profile_image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''
        cursor.execute(sql)
        conn.commit()

# ユーザーの追加
def add_user(conn, user: User):
    with conn.cursor() as cursor:
        sql = '''INSERT INTO users (display_name, bio, cognito_sub, profile_image_url) 
                 VALUES (%s, %s, %s, %s)'''
        cursor.execute(sql, (
            user.display_name,
            user.bio,
            user.cognito_sub,
            user.profile_image_url
        ))
        conn.commit()

# ユーザーの取得
def get_user_by_cognito_sub(conn, cognito_sub):
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = 'SELECT * FROM users WHERE cognito_sub = %s'
        cursor.execute(sql, (cognito_sub,))
        return cursor.fetchone()

# ユーザーの更新
def update_user(conn, user: User):
    with conn.cursor() as cursor:
        sql = '''UPDATE users 
                 SET display_name = %s, bio = %s, profile_image_url = %s 
                 WHERE cognito_sub = %s'''
        cursor.execute(sql, (
            user.display_name,
            user.bio,
            user.profile_image_url,
            user.cognito_sub
        ))
        conn.commit()