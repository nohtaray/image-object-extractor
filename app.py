import streamlit as st
import openai
from PIL import Image
import base64
import io
import json
import requests
from typing import List, Dict
import time
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

st.set_page_config(
    page_title="Object Extractor",
    page_icon="🎨",
    layout="wide"
)

def encode_image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def detect_objects(client: openai.OpenAI, image: Image.Image) -> List[Dict]:
    base64_image = encode_image_to_base64(image)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image thoroughly and identify ALL visible objects, including both large and small items, details, and parts of objects. Be comprehensive and include: main objects, background elements, small details, accessories, decorative items, furniture parts, natural elements, etc. If there are multiple objects of the same type, list each one separately with specific positions (for example: if there are 2 trees, list them as 'upper tree' and 'lower tree'). Please respond in the following JSON format: {\"objects\": [{\"object_ja\": \"object name in Japanese\", \"object_en\": \"object name in English\", \"position_ja\": \"position in Japanese (e.g., 右上, 中央, 左下)\", \"position_en\": \"position in English (e.g., upper right, center, lower left)\"}, ...]}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=1000
    )
    
    try:
        response_text = response.choices[0].message.content
        response_data = json.loads(response_text)
        
        # レスポンスからオブジェクトリストを取得
        if 'objects' in response_data:
            return response_data['objects']
        elif isinstance(response_data, list):
            return response_data
        else:
            # フォールバック: レスポンスの値から配列を探す
            for value in response_data.values():
                if isinstance(value, list):
                    return value
            return []
    except (json.JSONDecodeError, IndexError, AttributeError, KeyError) as e:
        st.error(f"オブジェクト検出の解析に失敗しました: {e}")
        return []


def generate_object_image(client: openai.OpenAI, original_image: Image.Image, obj: Dict, quality: str = "low", size: str = "1024x1024") -> str:
    # 画像編集用のプロンプト - アレンジ禁止、完全一致を要求（英語版を使用）
    object_en = obj.get('object_en', obj.get('object', ''))
    position_en = obj.get('position_en', obj.get('position', ''))
    prompt = f"Extract EXACTLY the {object_en} at {position_en} from this image. CRITICAL: Do not modify, enhance, stylize, or change ANYTHING about the {object_en}. Keep it 100% identical to the original - exact same colors, exact same textures, exact same lighting, exact same shadows, exact same proportions, exact same details, exact same angle, exact same orientation, exact same perspective, exact same viewpoint. Only remove the background and other objects by making them transparent. NO artistic interpretation, NO improvements, NO style changes, NO color adjustments, NO rotation, NO angle changes, NO perspective changes. Perfect pixel-level accuracy required. Maintain the EXACT same viewing angle and orientation as shown in the original image."
    
    # 元画像をバイト形式に変換（正しいMIMEタイプ指定）
    import io
    img_byte_arr = io.BytesIO()
    original_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # ファイルオブジェクトとして作成（MIMEタイプ指定）
    from io import BytesIO
    
    try:
        response = client.images.edit(
            model="gpt-image-1",
            image=("image.png", img_byte_arr, "image/png"),
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            output_format="png",
            background="transparent"
        )
        
        # レスポンスからデータを取得
        if response.data and len(response.data) > 0:
            first_item = response.data[0]
            
            # URLまたはb64_jsonの確認
            if hasattr(first_item, 'url') and first_item.url:
                return first_item.url
            elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                import base64
                # データURIスキーム形式で返す（Streamlitが表示可能）
                data_uri = f"data:image/png;base64,{first_item.b64_json}"
                return data_uri
            else:
                st.error("❌ URLもb64_jsonも見つかりません")
                return None
        else:
            st.error("❌ レスポンスデータが空です")
            return None
        
    except Exception as e:
        st.error(f"❌ gpt-image-1 エラー: {type(e).__name__}: {str(e)}")
        
        # エラーの詳細情報を表示
        if hasattr(e, 'response') and e.response is not None:
            st.write(f"HTTPステータス: {e.response.status_code}")
            try:
                error_body = e.response.json()
                st.write(f"エラー詳細: {error_body}")
            except:
                st.write(f"レスポンステキスト: {e.response.text}")
        
        st.write(f"プロンプト: {prompt}")
        return None

def download_image(url_or_data_uri: str) -> bytes:
    try:
        # データURIの場合の処理
        if url_or_data_uri.startswith("data:image/"):
            import base64
            # データURIからBase64部分を抽出
            base64_data = url_or_data_uri.split(",")[1]
            return base64.b64decode(base64_data)
        else:
            # 通常のURLの場合の処理
            response = requests.get(url_or_data_uri)
            response.raise_for_status()
            return response.content
    except Exception as e:
        st.error(f"画像ダウンロードエラー: {e}")
        return None

def main():
    st.title("🎨 Object Extractor")
    st.markdown("画像からオブジェクトを抽出し、個別の画像として再生成するツールです")
    
    # APIキーの取得（LOCAL=1の場合のみ環境変数から、それ以外はUI入力）
    st.sidebar.header("設定")
    
    # LOCAL環境変数をチェック
    is_local = os.getenv("LOCAL") == "1"
    
    if is_local:
        # LOCAL=1の場合、環境変数からAPIキーを取得
        env_api_key = os.getenv("OPENAI_API_KEY")
        if env_api_key:
            api_key = env_api_key
            st.sidebar.success("✅ APIキーが環境変数から読み込まれました")
        else:
            st.sidebar.error("❌ LOCAL=1が設定されていますが、OPENAI_API_KEYが見つかりません")
            api_key = None
    else:
        # LOCAL!=1の場合、UI入力を要求
        api_key = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password",
            help="OpenAI APIキーを入力してください"
        )
    
    # 画像生成設定
    st.sidebar.subheader("画像生成設定")
    image_quality = st.sidebar.selectbox(
        "画像品質",
        options=["high", "medium", "low"],
        index=1,
        help="high: 高品質, medium: 中品質（デフォルト）, low: 低品質"
    )
    
    image_size = st.sidebar.selectbox(
        "画像サイズ",
        options=["1024x1024", "1024x1536", "1536x1024"],
        index=0,
        help="1024x1024: 正方形, 1024x1536: 縦長, 1536x1024: 横長"
    )
    
    if not api_key:
        st.warning("OpenAI API キーを入力してください")
        return
    
    client = openai.OpenAI(api_key=api_key)
    
    # 画像アップロード
    st.header("📷 画像をアップロード")
    uploaded_file = st.file_uploader(
        "画像を選択してください",
        type=['png', 'jpg', 'jpeg'],
        help="PNG、JPG、JPEG形式の画像をアップロードできます"
    )
    
    if uploaded_file is not None:
        # 画像表示
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("アップロード画像")
            st.image(image, use_column_width=True)
        
        with col2:
            if st.button("🔍 オブジェクトを検出", type="primary"):
                with st.spinner("オブジェクトを検出中..."):
                    objects = detect_objects(client, image)
                
                if objects:
                    st.session_state.objects = objects
                    st.session_state.original_image = image
                    st.success(f"{len(objects)}個のオブジェクトを検出しました！")
                else:
                    st.error("オブジェクトの検出に失敗しました")
    
    # 検出されたオブジェクトの表示と選択
    if hasattr(st.session_state, 'objects') and st.session_state.objects:
        st.header("🎯 検出されたオブジェクト")
        
        # オブジェクト選択UI
        st.subheader("生成するオブジェクトを選択してください")
        
        # 全選択/全解除ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 全て選択"):
                for i in range(len(st.session_state.objects)):
                    st.session_state[f"select_obj_{i}"] = True
        with col2:
            if st.button("❌ 全て解除"):
                for i in range(len(st.session_state.objects)):
                    st.session_state[f"select_obj_{i}"] = False
        
        # 各オブジェクトの選択チェックボックス
        selected_objects = []
        for i, obj in enumerate(st.session_state.objects):
            key = f"select_obj_{i}"
            if key not in st.session_state:
                st.session_state[key] = False
            
            object_ja = obj.get('object_ja', obj.get('object', ''))
            object_en = obj.get('object_en', obj.get('object', ''))
            position_ja = obj.get('position_ja', obj.get('position', ''))
            position_en = obj.get('position_en', obj.get('position', ''))
            
            is_selected = st.checkbox(
                f"**{object_ja}** (位置: {position_ja})",
                value=st.session_state[key],
                key=key,
                help=f"英語: {object_en} at {position_en}"
            )
            
            if is_selected:
                selected_objects.append((i, obj))
        
        # 選択されたオブジェクトの画像生成
        if selected_objects:
            st.write(f"選択されたオブジェクト: {len(selected_objects)}個")
            
            # 現在の設定を表示
            st.info(f"画像設定: 品質={image_quality}, サイズ={image_size}")
            
            if st.button("🎨 選択したオブジェクトの画像を生成", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                if 'generated_images' not in st.session_state:
                    st.session_state.generated_images = {}
                
                for i, (obj_index, obj) in enumerate(selected_objects):
                    object_ja = obj.get('object_ja', obj.get('object', ''))
                    position_ja = obj.get('position_ja', obj.get('position', ''))
                    status_text.text(f"生成中: {object_ja} ({i+1}/{len(selected_objects)})")
                    
                    image_url = generate_object_image(client, st.session_state.original_image, obj, image_quality, image_size)
                    
                    if image_url and image_url != "None":
                        st.session_state.generated_images[f"{object_ja}_{position_ja}"] = image_url
                    else:
                        st.error(f"❌ {object_ja} の画像生成に失敗しました")
                    
                    progress_bar.progress((i + 1) / len(selected_objects))
                    time.sleep(1)  # API制限を考慮した待機
                
                status_text.text("生成完了！")
                st.success("選択したオブジェクトの画像生成が完了しました！")
        else:
            st.info("画像を生成するオブジェクトを選択してください。")
    
    # 生成された画像の表示とダウンロード
    if hasattr(st.session_state, 'generated_images') and st.session_state.generated_images:
        st.header("🖼️ 生成された画像")
        
        cols = st.columns(5)  # 5列に増加
        for i, (obj_key, image_url) in enumerate(st.session_state.generated_images.items()):
            with cols[i % 5]:
                st.write(f"**{obj_key.replace('_', ' - ')}**")
                
                try:
                    st.image(image_url, width=150)  # 固定幅で小さく表示
                except Exception as e:
                    st.error(f"画像表示エラー: {e}")
                
                # ダウンロードボタン
                image_data = download_image(image_url)
                if image_data:
                    st.download_button(
                        label="💾",  # ボタンも小さく
                        data=image_data,
                        file_name=f"{obj_key}.png",
                        mime="image/png",
                        key=f"download_{i}"
                    )

if __name__ == "__main__":
    main()
