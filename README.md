# AWS ブログアプリ

## 構成
- **EC2** (Amazon Linux 2023 / t3.micro) : Webサーバー
- **RDS** MySQL (db.t3.micro) : データベース
- **S3** : 画像ストレージ
- **VPC** : パブリック/プライベートサブネット設計

## 使用技術
- Python / Flask
- MySQL / PyMySQL
- AWS SDK (boto3)
- Docker / Docker Compose

## 機能
- 記事の投稿・表示・削除
- S3への画像アップロード・表示
- RDSへのデータ永続化

## AWS構成図
- パブリックサブネット: EC2
- プライベートサブネット: RDS
- S3: 画像ストレージ
- セキュリティグループによるアクセス制御
