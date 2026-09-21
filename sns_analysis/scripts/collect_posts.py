# -*- coding: utf-8 -*-
"""
collect_posts.py ― Bluesky の投稿をターミナルからまとめて収集する（プロジェクト用）

bsky_config.ini（ハンドル名・アプリパスワード）があれば自動でログインして取得する．

使い方（Anaconda Prompt，sns_analysis フォルダで）:
    python scripts/collect_posts.py --query 防災 --max 1000 --out data/bosai.csv          # 新しい順に最大1000件
    python scripts/collect_posts.py --query 防災 --query 観光 --max 500 --out data/posts.csv
    python scripts/collect_posts.py --query 防災 --method period --days 7 --window 6 --out data/bosai.csv   # 期間分割
    python scripts/collect_posts.py --author chunichi.bsky.social --max 300 --out data/chunichi.csv
    python scripts/collect_posts.py --query 防災 --max 500 --out data/bosai.csv --append   # 既存CSVに追記（重複除去）

--method paged  : cursor で続きを取得（既定．ログインが必要）
--method period : --days 日分を --window 時間ごとに区切って検索（ログイン不要．1窓100件まで）
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # sns_analysis/ を import パスに
from bsky_utils import (search_posts_paged, search_posts_by_period, get_author_posts,  # noqa: E402
                        save_posts, load_posts, login_status)


def main():
    ap = argparse.ArgumentParser(description="Bluesky 投稿の収集")
    ap.add_argument("--query", action="append", default=[], help="検索語（複数可）")
    ap.add_argument("--author", action="append", default=[], help="アカウントのハンドル（複数可）")
    ap.add_argument("--method", default="paged", choices=["paged", "period"], help="取得方法")
    ap.add_argument("--max", type=int, default=500, help="検索語／アカウント1つあたりの最大件数（paged）")
    ap.add_argument("--days", type=int, default=3, help="直近何日分を集めるか（period）")
    ap.add_argument("--window", type=int, default=12, help="検索窓の幅（時間）（period）")
    ap.add_argument("--sort", default="latest", choices=["latest", "top"])
    ap.add_argument("--out", default="data/posts.csv")
    ap.add_argument("--append", action="store_true", help="既存の CSV に追記し，重複を除く")
    args = ap.parse_args()

    if not args.query and not args.author:
        ap.error("--query か --author を少なくとも1つ指定してください")

    login_status()
    frames = []
    for q in args.query:
        print(f"=== 検索語: {q}")
        if args.method == "paged":
            frames.append(search_posts_paged(q, max_posts=args.max, sort=args.sort))
        else:
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
        note = (f"queries={args.query} authors={args.author} method={args.method} max={args.max} "
                f"days={args.days} window={args.window}h sort={args.sort}")
        save_posts(df, args.out, note=note)
        print(df["query"].value_counts())
    else:
        print("投稿を取得できませんでした．")


if __name__ == "__main__":
    main()
