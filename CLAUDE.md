# Object Extractor プロジェクト

OpenAI APIを使用して画像からオブジェクトを検出し、個別の画像として再生成するStreamlitツールです。

## プロジェクト概要

- **技術スタック**: Python, Streamlit, OpenAI API (GPT-4o, gpt-image-1)
- **主要機能**: オブジェクト検出、画像生成、ダウンロード機能
- **セキュリティ**: 環境変数でAPIキー管理

## 重要なコマンド

- `pip install -r requirements.txt`: 依存関係のインストール
- `streamlit run app.py`: アプリケーションの起動
- `python -m streamlit run app.py`: 代替起動方法

## コード規約

- Python PEP 8に従う
- 型ヒントを使用 (typing module)
- エラーハンドリングを適切に実装
- セキュリティを重視（APIキーの適切な管理）

## API使用方法

- **オブジェクト検出**: GPT-4o with Vision (JSON mode使用)
- **画像生成**: gpt-image-1 (品質: high/medium/low, サイズ: 複数対応)

## API キー設定

- **LOCAL=1**: 環境変数 `OPENAI_API_KEY` からAPIキーを自動読み込み
- **LOCAL!=1 または未設定**: UIでAPIキーを手動入力

## セキュリティ注意事項

- `.env`ファイルは絶対にコミットしない
- APIキーは環境変数で管理
- Claude Codeの設定で機密ファイルを除外済み

## ファイル構成

- `app.py`: メインアプリケーション
- `requirements.txt`: Python依存関係
- `.env`: 環境変数設定（Git除外済み）
- `.claude/settings.json`: Claude Code設定