# -*- coding: utf-8 -*-
"""
collect_posts.py ― Bluesky の投稿をターミナルからまとめて収集する（プロジェクト用）

使い方（Anaconda Prompt，sns_analysis フォルダで）:
    python scripts/collect_posts.py --query 防災 --days 7 --window 6 --out data/bosai.csv
    python scripts/collect_posts.py --query 防災 --query 観光 --days 3 --window 12 --out data/posts.csv
    python scripts/collect_posts.py --author chunichi.bsky.social --max 300 --out data/chunichi.csv
    python scripts/collect_posts.py --query 防災 --days 7 --out data/bosai.csv --append   # 既存CSVに追記（重複除去）

--window は検索窓の時間幅（時間）．投稿の多い語ほど小さくする（100件に達する窓が出たら小さくする）．
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # sns_analysis/ を import パスに
from bsky_utils import search_posts_by_period, get_author_posts, save_posts, load_posts  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Bluesky 投稿の収集")
    ap.add_argument("--query", action="append", default=[], help="検索語（複数可）")
    ap.add_argument("--author", action="append", default=[], help="アカウントのハンドル（複数可）")
    ap.add_argument("--days", type=int, default=3, help="直近何日分を集めるか")
    ap.add_argument("--window", type=int, default=12, help="検索窓の幅（時間）")
    ap.add_argument("--max", type=int, default=200, help="アカウント1つあたりの最大件数")
    ap.add_argument("--sort", default="latest", choices=["latest", "top"])
    ap.add_argument("--out", default="data/posts.csv")
    ap.add_argument("--append", action="store_true", help="既存の CSV に追記し，重複を除く")
    args = ap.parse_args()

    if not args.query and not args.author:
        ap.error("--query か --author を少なくとも1つ指定してください")

    frames = []
    for q in args.query:
        print(f"=== 検索語: {q}")
        frames.append(search_posts_by_period(q, days=args.days, hours_per_window=args.window, sort=args.sort))
    for a in args.author:
        print(f"=== アカウント: {a}")
        frames.append(get_author_posts(a, max_posts=args.max))

    df = pd.concat([f for f in frames if len(f)], ignore_index=True) if any(len(f) for f in frames) else pd.DataFrame()
    if args.append and Path(args.out).exists():
        old = load_posts(args.out)
        df = pd.concat([old, df], ignore_index=True)
    if len(df):
        df = df.drop_duplicates("post_uri").sort_values("created_at").reset_index(drop=True)
        note = f"queries={args.query} authors={args.author} days={args.days} window={args.window}h sort={args.sort}"
        save_posts(df, args.out, note=note)
        print(df["query"].value_counts())
    else:
        print("投稿を取得できませんでした．")


if __name__ == "__main__":
    main()
