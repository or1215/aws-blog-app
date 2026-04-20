import os
import hmac
import hashlib
import base64
import boto3
from botocore.exceptions import ClientError

# Cognito設定
COGNITO_REGION = os.environ.get('COGNITO_REGION')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

def get_cognito():
    """Cognitoクライアントを取得する"""
    return boto3.client('cognito-idp', region_name=COGNITO_REGION)

def get_secret_hash(username):
    """Cognitoのシークレットハッシュを生成する"""
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        COGNITO_CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def sign_up(email, password, display_name, username):
    """ユーザー登録をCognitoに送信する"""
    try:
        cognito = get_cognito()
        cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'nickname', 'Value': display_name}
            ]
        )
        return True, None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_messages = {
            'UsernameExistsException'     : 'このメールアドレスはすでに登録されています。',
            'InvalidPasswordException'    : 'パスワードは8文字以上で、大文字・小文字・数字・記号を含めてください。',
            'InvalidParameterException'   : '入力内容に誤りがあります。メールアドレスの形式を確認してください。',
            'TooManyRequestsException'    : 'しばらく時間をおいてから再度お試しください。',
            'CodeDeliveryFailureException': 'メールの送信に失敗しました。メールアドレスを確認してください。',
        }
        return False, error_messages.get(error_code, 'エラーが発生しました。もう一度お試しください。')

def confirm_sign_up(username, code):
    """メール認証コードを確認する"""
    try:
        cognito = get_cognito()
        cognito.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
            ConfirmationCode=code
        )
        return True, None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_messages = {
            'CodeMismatchException'    : '認証コードが正しくありません。',
            'ExpiredCodeException'     : '認証コードの有効期限が切れています。再度登録してください。',
            'TooManyRequestsException' : 'しばらく時間をおいてから再度お試しください。',
        }
        return False, error_messages.get(error_code, 'エラーが発生しました。もう一度お試しください。')

def sign_in(email, password):
    """ログイン処理を行いユーザー情報を返す"""
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
        access_token = response['AuthenticationResult']['AccessToken']
        user_info = cognito.get_user(AccessToken=access_token)

        # ユーザー属性を取得
        cognito_sub = None
        display_name = 'ゲスト'
        for attr in user_info.get('UserAttributes', []):
            if attr['Name'] == 'sub':
                cognito_sub = attr['Value']
            elif attr['Name'] == 'nickname':
                display_name = attr['Value']

        return True, {
            'access_token': access_token,
            'cognito_sub': cognito_sub,
            'display_name': display_name,
            'email': email
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_messages = {
            'NotAuthorizedException'   : 'メールアドレスまたはパスワードが正しくありません。',
            'UserNotFoundException'    : 'メールアドレスまたはパスワードが正しくありません。',
            'UserNotConfirmedException': 'メール認証が完了していません。',
            'TooManyRequestsException' : 'しばらく時間をおいてから再度お試しください。',
        }
        return False, error_messages.get(error_code, 'エラーが発生しました。もう一度お試しください。')