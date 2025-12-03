"""
Google Custom Search APIを使用した画像収集スクリプト

使用前の準備:
1. Google Cloud Console (https://console.cloud.google.com/) でプロジェクトを作成
2. Custom Search APIを有効化
3. APIキーを作成
4. Programmable Search Engine (https://programmablesearchengine.google.com/) で検索エンジンを作成
   - 「画像検索」をオンにする
   - 「ウェブ全体を検索」を選択
5. 検索エンジンID (cx) を取得
"""

from __future__ import annotations

import os
import time
import requests
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, List, Optional


class GoogleImageCollector:
    """Google Custom Search APIを使用して画像を収集するクラス"""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key, search_engine_id):
        # type: (str, str) -> None
        """
        初期化
        
        Args:
            api_key: Google Cloud APIキー
            search_engine_id: Programmable Search EngineのID (cx)
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
    
    def search_images(
        self,
        query,
        num_images=10,
        start_index=1,
        image_size=None,
        image_type=None,
        file_type=None,
        safe_search="active"
    ):
        # type: (str, int, int, Optional[str], Optional[str], Optional[str], str) -> List[Dict]
        """
        画像を検索する
        
        Args:
            query: 検索クエリ
            num_images: 取得する画像数 (最大100、1回のリクエストで最大10)
            start_index: 検索結果の開始インデックス (1-100)
            image_size: 画像サイズ ('huge', 'icon', 'large', 'medium', 'small', 'xlarge', 'xxlarge')
            image_type: 画像タイプ ('clipart', 'face', 'lineart', 'stock', 'photo', 'animated')
            file_type: ファイル形式 ('jpg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico', 'raw')
            safe_search: セーフサーチ ('active', 'off')
            
        Returns:
            画像情報のリスト
        """
        all_results = []
        images_collected = 0
        current_start = start_index
        
        while images_collected < num_images and current_start <= 100:
            # 1回のリクエストで最大10件
            num_to_fetch = min(10, num_images - images_collected)
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "searchType": "image",
                "num": num_to_fetch,
                "start": current_start,
                "safe": safe_search
            }
            
            # オプションパラメータを追加
            if image_size:
                params["imgSize"] = image_size
            if image_type:
                params["imgType"] = image_type
            if file_type:
                params["fileType"] = file_type
            
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if "items" in data:
                    for item in data["items"]:
                        image_info = {
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "thumbnail_url": item.get("image", {}).get("thumbnailLink", ""),
                            "context_url": item.get("image", {}).get("contextLink", ""),
                            "width": item.get("image", {}).get("width", 0),
                            "height": item.get("image", {}).get("height", 0),
                            "file_size": item.get("image", {}).get("byteSize", 0),
                            "mime_type": item.get("mime", "")
                        }
                        all_results.append(image_info)
                        images_collected += 1
                        
                        if images_collected >= num_images:
                            break
                else:
                    print("検索結果がありません: start={}".format(current_start))
                    break
                    
            except requests.exceptions.RequestException as e:
                print("APIリクエストエラー: {}".format(e))
                break
            
            current_start += 10
            
            # レート制限を避けるため少し待機
            if images_collected < num_images:
                time.sleep(0.5)
        
        return all_results
    
    def download_images(
        self,
        image_results,
        output_dir,
        prefix="image",
        use_thumbnail=False,
        timeout=30
    ):
        # type: (List[Dict], str, str, bool, int) -> List[str]
        """
        検索結果から画像をダウンロードする
        
        Args:
            image_results: search_imagesの結果
            output_dir: 保存先ディレクトリ
            prefix: ファイル名のプレフィックス
            use_thumbnail: サムネイルをダウンロードするか
            timeout: タイムアウト秒数
            
        Returns:
            ダウンロードに成功したファイルパスのリスト
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        total = len(image_results)
        
        for i, image_info in enumerate(image_results, 1):
            url = image_info["thumbnail_url"] if use_thumbnail else image_info["url"]
            
            if not url:
                print("[{}/{}] URLが空です、スキップします".format(i, total))
                continue
            
            # ファイル拡張子を決定
            ext = self._get_extension(url, image_info.get("mime_type", ""))
            filename = "{}_{:04d}{}".format(prefix, i, ext)
            filepath = output_path / filename
            
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(url, headers=headers, timeout=timeout, stream=True)
                response.raise_for_status()
                
                # Content-Typeを確認
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    print("[{}/{}] 画像ではありません: {}".format(i, total, content_type))
                    continue
                
                with open(str(filepath), "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                downloaded_files.append(str(filepath))
                print("[{}/{}] ダウンロード完了: {}".format(i, total, filename))
                
            except requests.exceptions.RequestException as e:
                print("[{}/{}] ダウンロード失敗: {}".format(i, total, e))
            except IOError as e:
                print("[{}/{}] ファイル保存エラー: {}".format(i, total, e))
            
            # サーバー負荷軽減のため少し待機
            time.sleep(0.3)
        
        return downloaded_files
    
    def _get_extension(self, url, mime_type):
        # type: (str, str) -> str
        """URLまたはMIMEタイプから拡張子を取得"""
        mime_to_ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
            "image/svg+xml": ".svg"
        }
        
        if mime_type in mime_to_ext:
            return mime_to_ext[mime_type]
        
        # URLから拡張子を取得
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"]:
            if path.endswith(ext):
                return ext if ext != ".jpeg" else ".jpg"
        
        return ".jpg"  # デフォルト


def main():
    """使用例"""
    # APIキーと検索エンジンIDを直接指定    
    API_KEY = "YOUR_API_KEY_HERE"
    SEARCH_ENGINE_ID = "YOUR_SEARCH_ENGINE_ID_HERE"
    
    # コレクターを初期化
    collector = GoogleImageCollector(API_KEY, SEARCH_ENGINE_ID)
    
    # 検索クエリ
    query = "cute cat"
    
    print("検索クエリ: {}".format(query))
    print("-" * 40)
    
    # 画像を検索 (最大20枚)
    results = collector.search_images(
        query=query,
        num_images=100,
        image_size="large",
        safe_search="active"
    )
    
    print("検索結果: {}件".format(len(results)))
    
    # 検索結果を表示
    for i, img in enumerate(results, 1):
        print("\n[{}] {}...".format(i, img['title'][:50]))
        print("    URL: {}...".format(img['url'][:80]))
        print("    サイズ: {}x{}".format(img['width'], img['height']))
    
    # 画像をダウンロード
    if results:
        print("\n" + "-" * 40)
        print("画像をダウンロードしています...")
        
        downloaded = collector.download_images(
            image_results=results,
            output_dir="./downloaded_images",
            prefix="cat"
        )
        
        print("\nダウンロード完了: {}/{}件".format(len(downloaded), len(results)))


if __name__ == "__main__":
    main()
