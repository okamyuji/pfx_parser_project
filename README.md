# pfx_parser_project

## プロジェクト概要

- このプロジェクトは、クライアント証明書認証におけるpfx/p12形式の証明書ファイルを解析し、証明書内のCommon Name (CN) からユーザーIDを抽出する Django REST Framework (DRF) API サーバーです。
- 主に開発・テスト環境での利用を想定しており、Flutterなどのクライアントアプリケーションからpfx/p12ファイルを送信し、サーバー側でユーザーIDを取得する動作検証を行うことができます。

## 開発環境構築手順

### 前提条件

- Python 3.11 以上
- pip (Python パッケージ管理ツール)

### 手順

1. **リポジトリのクローン**

    ```bash
    git clone https://github.com/okamyuji/pfx_parser_project.git
    cd pfx_parser_project
    ```

2. **仮想環境の作成と有効化**

    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate  # Windows
    ```

3. **Python パッケージのインストール**

    ```bash
    pip install -r requirements.txt
    ```

    `requirements.txt` には、以下のパッケージが記述されています。

    ```txt
    Django==5.1
    djangorestframework==3.15.2
    cryptography==44.0.0
    pyOpenSSL  # cryptography で pfx を扱うために必要となる場合がある
    ```

4. **Django アプリケーションの設定**

    `pfx_parser_project/settings.py`、`pfx_parser_app/apps.py`、`pfx_parser_app/urls.py`、`pfx_parser_app/views.py` は、このリポジトリに初期設定済みのものが含まれています。必要に応じて設定を調整してください。

    - `pfx_parser_project/settings.py`:  `INSTALLED_APPS` に `pfx_parser_app` が追加されていることを確認してください。
    - `pfx_parser_app/apps.py`:  アプリケーション設定クラス `PfxParserAppConfig` が定義されています。
    - `pfx_parser_app/urls.py`:  API エンドポイント `/api/parse_pfx/` のルーティングが定義されています。
    - `pfx_parser_app/views.py`:  pfx/p12 ファイル解析処理を行う `parse_pfx` ビュー関数が実装されています。

5. **マイグレーションの実行 (必要に応じて)**

    このプロジェクトではデータベースを使用しませんが、Django の基本的な設定としてマイグレーションが必要となる場合があります。

    ```bash
    python manage.py migrate
    ```

## テストの実行

- テストの実行方法

```bash
python manage.py test pfx_parser_app.tests
```

## API の実行方法

1. **Django 開発サーバーの起動**

    ```bash
    python manage.py runserver
    ```

    サーバーは `http://127.0.0.1:8000/` で起動します。

2. **API リクエストの送信 (curl コマンド例)**

    p12 ファイルを送信してユーザーIDを取得するには、以下の curl コマンドを実行します。

    **パスワードなしの p12 ファイルの場合**

    ```bash
    curl -X POST -F "file=@/path/to/your/certificate.p12" "http://127.0.0.1:8000/api/parse_pfx/"
    ```

    **パスワード付きの p12 ファイルの場合**

    ```bash
    curl -X POST -F "file=@/path/to/your/certificate.p12" -F "password=your_password" "http://127.0.0.1:8000/api/parse_pfx/"
    ```

    - `/path/to/your/certificate.p12` は、実際の p12 ファイルのパスに置き換えてください。
    - `your_password` は、p12 ファイルに設定したパスワード (パスワード付きの場合) に置き換えてください。

    **成功した場合のレスポンス例**

    ```json
    {"user_id": "testuser"}
    ```

    `user_id` には、証明書の Common Name (CN) から抽出されたユーザーIDが返されます。

## 検証用証明書の作成手順

開発・テスト用にパスワード付き p12 ファイル (`output.p12`) を作成する手順を以下に示します。事前に OpenSSL がインストールされている必要があります。

1. **秘密鍵の生成 (`private.key`)**

    ```bash
    openssl genrsa -out private.key 2048
    ```

2. **証明書署名要求 (CSR) の作成 (`private.csr`)**

    ```bash
    openssl req -new -key private.key -out private.csr
    ```

    コマンド実行後、証明書に関する情報が対話的に求められます。

    - **Common Name (CN)** には、ユーザーIDとして抽出したい文字列 (例: `testuser`) を入力してください。
    - その他の項目は、開発・テスト用途であれば適当な値を入力しても構いません。

    例:

    ```sh
    Country Name (2 letter code) [AU]:JP
    State or Province Name (full name) [Some-State]:Tokyo
    Locality Name (eg, city) []:Nerima-ku
    Organization Name (eg, company) [Internet Widgits Pty Ltd]:Example Corp.
    Organizational Unit Name (eg, section) []:Development
    Common Name (e.g. server FQDN or YOUR name) []:testuser  # ★ユーザーID (CN)
    Email Address []:test@example.com
    Please enter the following 'extra' attributes

    to be sent with your certificate request
    A challenge password []: # チャレンジパスワード (任意、通常は空欄でEnter)
    An optional company name []: # オプションの会社名 (任意、通常は空欄でEnter)
   ```

3. **自己署名証明書の生成 (`certificate.crt`)**

    ```bash
    openssl x509 -req -in private.csr -signkey private.key -out certificate.crt -days 365
    ```

4. **p12 ファイルの作成 (`output.p12`)**

    ```bash
    openssl pkcs12 -export -out output.p12 -inkey private.key -in certificate.crt -passout pass:password123
    ```

    このコマンドで、パスワード `password123` で保護された `output.p12` ファイルが作成されます。

    作成された `output.p12` ファイルを curl コマンドで送信して API の動作を確認してください。

## 注意事項

- **自己署名証明書は開発・テスト環境専用です。** 実運用環境では、認証局 (CA) から発行された正式な証明書を使用してください。自己署名証明書を実運用環境で使用すると、セキュリティ上のリスクが発生します。
- このプロジェクトは、pfx/p12 ファイルの解析とユーザーID抽出の検証を目的としています。**本番環境での利用を想定した堅牢な実装ではありません。** 本番環境に適用する際は、セキュリティ、エラー処理、パフォーマンスなどを十分に考慮し、必要に応じてコードを修正してください。
