# AWS ブログアプリ

AWSの主要サービスを活用したブログ管理システムです。
EC2・RDS・S3・CloudFront・Cognitoなど複数のAWSサービスを組み合わせ、セキュアかつスケーラブルなWebアプリケーションを個人で構築しました。
また、GitHub ActionsによるCI/CDパイプラインを構築し、Actions Secrets and Variablesを活用して機密情報を安全に管理しながら、
mainブランチへのプッシュで本番環境へ自動デプロイされる開発フローを実現しました。

---

## 構成

### AWSインフラ

| サービス | 用途 | スペック |
|---|---|---|
| EC2 | Webサーバー・アプリケーションサーバー | Amazon Linux 2023 / t3.micro |
| RDS | データベースサーバー | MySQL / db.t3.micro |
| S3 | 画像ファイルのストレージ | blog-images-2026 |
| CloudFront | CDN・画像キャッシュ配信 | blog-images-cdn |
| Amazon Cognito | ユーザー認証・メール認証 | User Pool |
| VPC | ネットワーク設計・サブネット分離 | パブリック/プライベートサブネット |
| IAM | 権限管理・ロール設計 | 最小権限の原則 |

### ネットワーク構成

```
インターネット
      ↓
インターネットゲートウェイ
      ↓
パブリックサブネット (10.0.1.0/24)
      ↓
EC2 (blog-server) t3.micro
      ↓
プライベートサブネット (10.0.2.0/24)
      ↓
RDS MySQL (blog-db) db.t3.micro

S3 (blog-images-2026)
      ↓
CloudFront (CDN)
```

---

## 使用技術

### バックエンド

| 技術 | 用途 |
|---|---|
| Python | メイン言語 |
| Flask | Webフレームワーク |
| PyMySQL | MySQLドライバ |
| boto3 | AWS SDK |
| python-dotenv | 環境変数管理 |
| Jinja2 | テンプレートエンジン |

---

### 開発ツール

| ツール | 用途 |
|---|---|
| Docker / Docker Compose | ローカル開発環境 |
| Git / GitHub | バージョン管理 |
| GitHub Actions | CI/CDパイプライン |
| VSCode | エディタ |

---

## 機能

- ユーザー登録・メール認証・ログイン・ログアウト（AWS Cognito）
- 記事の投稿・一覧表示・詳細表示・削除
- サムネイル画像のアップロード（S3）・CloudFront経由での高速配信
- プロフィール編集
- ログイン必須ページの保護

---

## セキュリティ設計

| 項目 | 設定 |
|---|---|
| EC2 SSH | 自分のIP + EC2 Instance Connect のみ許可 |
| RDS | EC2からのみアクセス可能（Port 3306） |
| S3 | CloudFrontからのみアクセス可能（パブリックアクセスブロック） |
| 認証情報 | .envファイルで管理・GitHubには非公開 |
| CI/CD secrets | GitHub Actions Secrets and Variablesで管理 |
| Cognito | メール認証・SECRET_HASHによるセキュアなAPI認証 |

---

## CI/CD

GitHub Actionsを用いたCI/CDパイプラインを構築しています。

```
git push origin main
      ↓
GitHub Actionsが自動実行
      ↓
EC2にSSH接続
      ↓
git pull / pip install / systemctl restart
      ↓
本番環境に自動反映
```

- Actions Secrets and Variablesで機密情報（SSHキー・ホスト情報）を安全に管理
- systemdでFlaskアプリをサービス管理・自動再起動

---

## フォルダ構成

```
blog-app/
├── app.py                   # ルーティングのみ
├── db/
│   ├── posts.py             # 投稿関連SQL
│   └── users.py             # ユーザー関連SQL
├── services/
│   └── cognito.py           # Cognito認証処理
├── public/
│   ├── static/
│   │   └── css/
│   └── templates/
│       ├── base.html        # 共通レイアウト
│       ├── index.html       # 記事一覧
│       ├── new_post.html    # 新規投稿
│       ├── post_detail.html # 記事詳細
│       ├── login.html       # ログイン
│       ├── register.html    # 新規登録
│       ├── confirm.html     # メール認証
│       └── edit_profile.html# プロフィール編集
├── private/
│   └── .env                 # 環境変数（非公開）
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```