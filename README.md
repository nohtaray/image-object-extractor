# Object Extractor

OpenAI APIを使用して、画像からオブジェクトを検出し、それぞれのオブジェクトを単体で再生成するStreamlitツールです。

## 機能

1. **オブジェクト検出**: GPT-4 Visionを使用して画像内のオブジェクトとその位置を特定
2. **画像再生成**: DALL-E 3を使用して各オブジェクトを背景透過で単体生成
3. **Web UI**: Streamlitによる直感的なユーザーインターフェース
4. **ダウンロード機能**: 生成された画像をPNG形式でダウンロード可能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. OpenAI APIキーの準備

OpenAIのAPIキーが必要です。[OpenAI Platform](https://platform.openai.com/)でアカウントを作成し、APIキーを取得してください。

### 3. 環境変数の設定

`.env`ファイルに取得したAPIキーを設定してください：

```bash
# .env ファイルを編集
OPENAI_API_KEY=your_actual_openai_api_key_here
```

**重要**: `.env`ファイルには実際のAPIキーを記載し、GitHubなどにコミットしないでください。

### 4. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセスしてください。

## 使用方法

1. **APIキー**: 環境変数から自動読み込み（手動入力も可能）
2. **画像アップロード**: PNG、JPG、JPEG形式の画像をアップロード
3. **オブジェクト検出**: 「オブジェクトを検出」ボタンをクリック
4. **画像生成**: 「全てのオブジェクト画像を生成」ボタンをクリック
5. **ダウンロード**: 生成された各画像をダウンロード

## 必要なAPI

- **OpenAI GPT-4 Vision**: オブジェクト検出用
- **OpenAI DALL-E 3**: 画像生成用

## 注意事項

- OpenAI APIの使用料金が発生します
- 大量のオブジェクトがある画像では処理時間が長くなる場合があります
- API制限により、連続生成時に待機時間が発生する場合があります