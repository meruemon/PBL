# -*- coding: utf-8 -*-
"""
download_images.py ― 【参考資料】取得済みの投稿 CSV から，画像付き投稿の画像をまとめてダウンロードする

注意: SNS の画像にはセンシティブな内容（性的・暴力的・不快な画像）が含まれることがある．
      授業の本編では扱わない．使う場合は教員に相談し，少量から確認しながら進めること．
      モデレーション／自己申告ラベルが付いた投稿は既定で除外する（--include-labeled で含める）．

使い方（Anaconda Prompt，sns_analysis フォルダで）:
    python scripts/download_images.py --csv data/posts.csv --out data/images --max-posts 100
    python scripts/download_images.py --csv data/posts.csv --query 観光 --size fullsize --max-posts 50
    python scripts/download_images.py --csv data/posts.csv --first-only --max-images 200

--size thumb    : 長辺 1000px 程度（既定．分析には十分，容量が小さい）
--size fullsize : 最大 2000px（細部を見たいとき）
保存済みの画像は再取得しないので，何度実行しても同じ結果になる．一覧は <out>/images.csv に書き出される．
画像は授業内でのみ利用し，再配布しない．発表には画像そのものではなく集計結果を載せる．
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # sns_analysis/ を import パスに
from bsky_utils import load_posts, download_images  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Bluesky 投稿画像のダウンロード")
    ap.add_argument("--csv", default="data/posts.csv", help="save_posts で保存した投稿 CSV")
    ap.add_argument("--out", default="data/images", help="保存先フォルダ")
    ap.add_argument("--query", action="append", default=[], help="この検索語の投稿だけ対象にする（複数可）")
    ap.add_argument("--max-posts", type=int, default=100, help="画像を取りに行く投稿数の上限")
    ap.add_argument("--max-images", type=int, default=None, help="保存する総枚数の上限")
    ap.add_argument("--size", default="thumb", choices=["thumb", "fullsize"])
    ap.add_argument("--first-only", action="store_true", help="各投稿の1枚目だけ保存する")
    ap.add_argument("--include-labeled", action="store_true", help="ラベル付き（センシティブの可能性）の投稿も含める")
    args = ap.parse_args()

    df = load_posts(args.csv)
    if args.query:
        df = df[df["query"].isin(args.query)]
    n_img_posts = int((df["image_count"].fillna(0) > 0).sum())
    print(f"対象 {len(df)} 件のうち画像付き {n_img_posts} 件（画像の総数 {int(df['image_count'].fillna(0).sum())} 枚）")
    images = download_images(df, out_dir=args.out, max_posts=args.max_posts, size=args.size,
                             all_images=not args.first_only, max_images=args.max_images,
                             skip_labeled=not args.include_labeled)
    if len(images):
        print(images[["post_id", "image_index", "width", "height", "bytes"]].describe(include="all").loc[["count", "mean", "max"]].round(0))


if __name__ == "__main__":
    main()
