# -*- coding: utf-8 -*-
"""
bsky_utils.py  ―  Bluesky の公開データを集めて分析するための「道具箱」

データサイエンス基礎・応用PBL（吉田班）SNS分析テーマ用の共通モジュールです．
Notebook からは次のように読み込んで使います．

    from bsky_utils import *

設計方針
--------
* 各自の Bluesky アカウント（無料）と「アプリパスワード」でログインして使う．
  ハンドル名とアプリパスワードは同じフォルダの bsky_config.ini に書く（Git 管理外）．
  最初の API 呼び出し時に自動でログインする．設定ファイルが無い／ログインに失敗したときは
  公開ホスト（ログイン不要）にフォールバックするが，公開ホストは学内ネットワーク等から
  拒否（403）されることがあり，続きの取得（cursor）もできない．
* API仕様の変更に備え，APIアクセスはこのファイルに集約する．Notebookは道具を呼ぶだけ．
* 投稿検索（searchPosts）は「1回の検索で最大100件」．続きは cursor で取得する
  （search_posts_paged）．期間を区切って集めたいときは since/until（search_posts_by_period）．
* 取得したデータは授業内だけで扱う．発表資料にはハンドル名や投稿URLを載せない
  （anonymize() でハッシュ化できる）．

動作確認: 2026-09-21（公開ホスト，jetstream2）／ログイン方式は 2026-09 に実アカウントで確認
"""
from __future__ import annotations

import configparser
import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

# ----------------------------------------------------------------------
# 基本設定
# ----------------------------------------------------------------------

# 公開AppViewのホスト（ログインしていないとき用）．先頭から順に試す．
PUBLIC_HOSTS = ["https://api.bsky.app", "https://public.api.bsky.app"]
HOSTS = list(PUBLIC_HOSTS)          # 現在のアクセス先（ログインすると自分の PDS に置き換わる）

# 相手のサーバに「誰がアクセスしているか」を伝える（マナー）
HEADERS = {"User-Agent": "KansaiU-DataScience-PBL/2026 (education)"}

# ハンドル名とアプリパスワードを書く設定ファイル（このファイルと同じフォルダ）
CONFIG_PATH = Path(__file__).resolve().parent / "bsky_config.ini"

JST = timezone(timedelta(hours=9))

# 日本語文字（ひらがな・カタカナ・漢字）を含むかどうかの判定用
_JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
_URL_RE = re.compile(r"https?://\S+")
_MENTION_RE = re.compile(r"(?<!\w)@[A-Za-z0-9._:-]+")

# ログイン状態（モジュール内で共有）
_session = {"attempted": False, "logged_in": False, "handle": None, "did": None,
            "pds": None, "refresh_jwt": None, "config": None}


# ----------------------------------------------------------------------
# ログイン（設定ファイル → 自動）
# ----------------------------------------------------------------------

def load_config(path: str | Path = CONFIG_PATH) -> dict | None:
    """bsky_config.ini から handle と app_password を読む．無い／未記入なら None．"""
    path = Path(path)
    if not path.exists():
        # よくある間違い：Windows で拡張子が隠れて bsky_config.ini.ini / .txt になっている
        for wrong in (path.with_name(path.name + ".ini"), path.with_name(path.name + ".txt"),
                      path.with_name(path.stem + ".txt")):
            if wrong.exists():
                print(f"設定ファイルの名前が {wrong.name} になっています．{path.name} に変更してください（今回はこのまま読み込みます）．")
                path = wrong
                break
        else:
            return None
    cp = configparser.ConfigParser()
    cp.read(path, encoding="utf-8")
    if "bluesky" not in cp:
        return None
    def clean(v: str) -> str:   # 前後の空白と引用符（" '）を取り除く
        return v.strip().strip('"').strip("'").strip()

    handle = clean(cp["bluesky"].get("handle", "")).lstrip("@")
    pw = clean(cp["bluesky"].get("app_password", ""))
    if not handle or not pw or handle.startswith("your-") or pw.startswith("xxxx"):
        return None
    return {"handle": handle, "app_password": pw,
            "pds": clean(cp["bluesky"].get("pds", "https://bsky.social")) or "https://bsky.social"}


def login(handle: str, app_password: str, pds: str = "https://bsky.social", verbose: bool = True) -> dict:
    """Blueskyアカウントでログインし，以後のAPIアクセスを認証付きにする．

    通常は bsky_config.ini に書いておけば自動で呼ばれるので，直接呼ぶ必要はない．
    * app_password は Bluesky の「設定 → プライバシーとセキュリティ → アプリパスワード」で
      発行した専用パスワード．通常のログインパスワードは絶対に使わない．
    * ログインしても取得できるのは公開投稿だけで，データの扱いのルールは変わらない．
    """
    r = requests.post(f"{pds}/xrpc/com.atproto.server.createSession",
                      json={"identifier": handle, "password": app_password},
                      headers={"User-Agent": HEADERS["User-Agent"]}, timeout=20)
    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text[:200])
        except Exception:
            msg = r.text[:200]
        raise RuntimeError(f"ログイン失敗 {r.status_code}: {msg}")
    session = r.json()
    endpoint = pds
    for svc in (session.get("didDoc") or {}).get("service", []):
        if svc.get("id", "").endswith("atproto_pds") and svc.get("serviceEndpoint"):
            endpoint = svc["serviceEndpoint"]
    HOSTS[:] = [endpoint]                      # 以後は自分のPDS経由でアクセス（AppViewへ中継される）
    HEADERS["Authorization"] = f"Bearer {session['accessJwt']}"
    _session.update({"attempted": True, "logged_in": True, "handle": session.get("handle"),
                     "did": session.get("did"), "pds": endpoint, "refresh_jwt": session.get("refreshJwt"),
                     "config": {"handle": handle, "app_password": app_password, "pds": pds}})
    if verbose:
        print(f"ログインしました: @{session.get('handle')}（アクセス先: {endpoint}）")
    return {"handle": session.get("handle"), "did": session.get("did")}


def login_from_config(path: str | Path = CONFIG_PATH, verbose: bool = True) -> bool:
    """設定ファイルを読んでログインする．成功すれば True．"""
    _session["attempted"] = True
    cfg = load_config(path)
    if cfg is None:
        if verbose:
            print(f"設定ファイル {Path(path).name} が無いか未記入です．公開ホスト（ログインなし）で続行します．\n"
                  "  → bsky_config.example.ini をコピーして bsky_config.ini を作り，ハンドル名とアプリパスワードを記入してください．")
        return False
    try:
        login(cfg["handle"], cfg["app_password"], pds=cfg["pds"], verbose=verbose)
        return True
    except (RuntimeError, requests.RequestException) as e:
        print(f"ログインに失敗しました: {e}\n  公開ホスト（ログインなし）で続行します．bsky_config.ini の内容を確認してください．")
        return False


def _ensure_login() -> None:
    """最初の API 呼び出し時に一度だけ，設定ファイルからログインを試みる．"""
    if not _session["attempted"]:
        login_from_config()


def _refresh_session() -> bool:
    """アクセストークンの期限切れ（約2時間）に対応して更新する．駄目なら再ログイン．"""
    if _session.get("refresh_jwt"):
        r = requests.post(f"{_session['pds']}/xrpc/com.atproto.server.refreshSession",
                          headers={"Authorization": f"Bearer {_session['refresh_jwt']}",
                                   "User-Agent": HEADERS["User-Agent"]}, timeout=20)
        if r.status_code == 200:
            s = r.json()
            HEADERS["Authorization"] = f"Bearer {s['accessJwt']}"
            _session["refresh_jwt"] = s.get("refreshJwt")
            return True
    cfg = _session.get("config")
    if cfg:
        try:
            login(cfg["handle"], cfg["app_password"], pds=cfg["pds"], verbose=False)
            return True
        except Exception:
            pass
    return False


def logout() -> None:
    """ログイン状態を解除し，公開ホストに戻す（以後，自動ログインはしない）．"""
    HOSTS[:] = list(PUBLIC_HOSTS)
    HEADERS.pop("Authorization", None)
    _session.update({"attempted": True, "logged_in": False, "handle": None, "refresh_jwt": None})
    print("公開ホスト（ログインなし）に戻しました．")


def login_status() -> dict:
    """いまログインしているか，どのホストにアクセスするかを表示して返す．"""
    _ensure_login()
    st = {"logged_in": _session["logged_in"], "handle": _session["handle"], "hosts": list(HOSTS)}
    if st["logged_in"]:
        print(f"ログイン中: @{st['handle']}  アクセス先: {HOSTS[0]}")
    else:
        print(f"ログインなし（公開ホスト）: {HOSTS}  ※ 403 が出る場合は bsky_config.ini を設定してください")
    return st


# ----------------------------------------------------------------------
# 低レベル：HTTP GET（ホスト切替・リトライ付き）
# ----------------------------------------------------------------------

def _get(endpoint: str, params: dict, timeout: int = 20, max_retries: int = 4) -> dict:
    """APIに GET し，JSON（dict）を返す（ログイン中なら自分の PDS 経由，そうでなければ公開ホスト）．

    * 429（アクセス過多）のときは Retry-After 秒だけ待って再試行する．
    * 403（アクセス拒否）は同じホストで少し待って再試行し，それでも駄目なら次のホストを試す．
    * 401（トークン期限切れ）はセッションを更新して再試行する．
    """
    _ensure_login()
    last_error = None
    refreshed = False
    for host in HOSTS:
        url = f"{host}/xrpc/{endpoint}"
        for attempt in range(max_retries):
            try:
                r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            except requests.RequestException as e:  # 通信エラー
                last_error = e
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 2 ** attempt))
                print(f"  アクセス過多(429)．{min(wait, 30)}秒待ちます…")
                time.sleep(min(wait, 30))
                continue
            if r.status_code == 403:
                last_error = RuntimeError(f"403 Forbidden: {host} {endpoint}")
                time.sleep(1.5 * (attempt + 1))   # 1.5, 3, 4.5, 6 秒待って同じホストで再試行
                continue
            if r.status_code == 401:
                if _session["logged_in"] and not refreshed and _refresh_session():
                    refreshed = True
                    continue
                raise RuntimeError("認証エラー（401）：bsky_config.ini のハンドル名・アプリパスワードを確認してください")
            # それ以外（400など）はパラメータの誤りが多いので内容を表示して停止
            try:
                msg = r.json().get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise RuntimeError(f"APIエラー {r.status_code}: {msg}")
    hint = "" if _session["logged_in"] else "\n  ログインなしの公開ホストは拒否されることがあります．bsky_config.ini を設定してください．"
    raise RuntimeError(f"Bluesky API にアクセスできませんでした: {last_error}{hint}")


# ----------------------------------------------------------------------
# 投稿（post）を1行の辞書に変換する
# ----------------------------------------------------------------------

def _extract_images(embed: dict) -> list[dict]:
    """埋め込み(embed)から画像のリスト [{thumb, fullsize, alt}, ...] を取り出す．"""
    if not embed:
        return []
    t = embed.get("$type", "")
    if t == "app.bsky.embed.images#view":
        return embed.get("images", [])
    if t == "app.bsky.embed.recordWithMedia#view":  # 引用＋画像
        return _extract_images(embed.get("media") or {})
    if t == "app.bsky.embed.gallery#view":  # ギャラリー形式
        return [{"thumb": it.get("thumbnail"), "fullsize": it.get("fullsize"), "alt": it.get("alt", "")}
                for it in embed.get("items", [])]
    return []


def post_to_row(post: dict, query: str = "") -> dict:
    """APIが返す投稿（dict）を，表の1行（dict）に変換する．"""
    record = post.get("record") or {}
    author = post.get("author") or {}
    embed = post.get("embed") or {}
    images = _extract_images(embed)
    text = str(record.get("text", ""))
    langs = record.get("langs") or []

    external = embed.get("external") if embed.get("$type") == "app.bsky.embed.external#view" else None
    video_thumb = embed.get("thumbnail") if embed.get("$type") == "app.bsky.embed.video#view" else ""

    return {
        "post_uri": post.get("uri", ""),
        "post_id": stable_hash(post.get("uri", "")),
        "author_handle": author.get("handle", ""),
        "author_id": stable_hash(author.get("did", "")),
        "author_name": author.get("displayName", ""),
        "created_at": record.get("createdAt"),
        "text": text,
        "langs": ",".join(langs) if isinstance(langs, list) else str(langs),
        "is_japanese": bool(_JP_RE.search(text)),
        "like_count": int(post.get("likeCount") or 0),
        "repost_count": int(post.get("repostCount") or 0),
        "reply_count": int(post.get("replyCount") or 0),
        "quote_count": int(post.get("quoteCount") or 0),
        "image_count": len(images),
        # モデレーション／投稿者自身が付けたラベル（porn, sexual, nudity, graphic-media など）．
        # 付いていれば，画像はセンシティブな可能性が高い．download_images() は既定で除外する．
        "labels": ",".join(sorted({l.get("val", "") for l in (post.get("labels") or [])} |
                                  {l.get("val", "") for l in ((record.get("labels") or {}).get("values") or [])}
                                  - {""})),
        "image_urls": "|".join((im.get("fullsize") or im.get("thumb") or "") for im in images),
        "image_thumbs": "|".join((im.get("thumb") or "") for im in images),
        "image_alts": "|".join((im.get("alt") or "").replace("|", " ") for im in images),
        "video_thumb": video_thumb or "",
        "external_url": (external or {}).get("uri", ""),
        "external_title": (external or {}).get("title", ""),
        "query": query,
    }


def posts_to_dataframe(posts: list[dict], query: str = "") -> pd.DataFrame:
    """投稿のリストを DataFrame にする．日本時間の列 created_at_jst も付ける．"""
    df = pd.DataFrame([post_to_row(p, query) for p in posts])
    if len(df):
        df = add_datetime_columns(df)
    return df


def add_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """created_at（文字列）から日本時間の列を作る（CSV読み込み後にも使える）．"""
    df = df.copy()
    ts = pd.to_datetime(df["created_at"], utc=True, format="ISO8601", errors="coerce")
    df["created_at_jst"] = ts.dt.tz_convert("Asia/Tokyo")
    df["date"] = df["created_at_jst"].dt.date
    df["hour"] = df["created_at_jst"].dt.hour
    df["weekday"] = df["created_at_jst"].dt.day_name()
    return df


# ----------------------------------------------------------------------
# 投稿の検索
# ----------------------------------------------------------------------

def search_posts(query: str, limit: int = 100, lang: str | None = "ja", sort: str = "latest",
                 since: str | None = None, until: str | None = None,
                 japanese_only: bool = True) -> pd.DataFrame:
    """キーワードで投稿を検索し，DataFrame で返す（1回の検索で最大100件）．

    query : 検索語．ハッシュタグは "#防災" のように書ける．
    sort  : "latest"（新しい順）または "top"（反応の多い順）
    since / until : "2026-09-01T00:00:00Z" のようなUTC時刻文字列で期間を絞る
    japanese_only : 本文に日本語文字を含む投稿だけ残す
    """
    limit = max(1, min(int(limit), 100))
    params = {"q": query, "limit": limit, "sort": sort}
    if lang:
        params["lang"] = lang
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    data = _get("app.bsky.feed.searchPosts", params)
    df = posts_to_dataframe(data.get("posts", []), query=query)
    if japanese_only and len(df):
        df = df[df["is_japanese"]].reset_index(drop=True)
    return df


def search_posts_paged(query: str, max_posts: int = 500, lang: str | None = "ja", sort: str = "latest",
                       since: str | None = None, until: str | None = None,
                       japanese_only: bool = True, pause: float = 0.5, verbose: bool = True) -> pd.DataFrame:
    """cursor（続きの取得）を使って，新しい順に最大 max_posts 件まで検索する（標準の大量取得）．

    ログインしていれば数千件まで連続取得できる．未ログインの公開ホストでは
    2ページ目以降が拒否（403）されるので，その場合は search_posts_by_period を使う．
    since / until を付ければ，期間内の投稿だけを新しい順に取得できる．
    """
    rows, cursor, page = [], None, 0
    while len(rows) < max_posts:
        params = {"q": query, "limit": 100, "sort": sort}
        if lang:
            params["lang"] = lang
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if cursor:
            params["cursor"] = cursor
        try:
            data = _get("app.bsky.feed.searchPosts", params, max_retries=4 if cursor is None else 2)
        except RuntimeError as e:
            if cursor is not None and "403" in str(e):
                print("  2ページ目以降の取得が拒否されました．ログインなしでは cursor が使えません．"
                      "bsky_config.ini を設定するか，search_posts_by_period() を使ってください．")
                break
            raise
        posts = data.get("posts", [])
        rows.extend(post_to_row(p, query=query) for p in posts)
        page += 1
        cursor = data.get("cursor")
        if verbose:
            print(f"  ページ{page}: {len(posts)}件（累計 {len(rows)}件）")
        if not cursor or not posts:
            break
        time.sleep(pause)
    df = pd.DataFrame(rows[:max_posts])
    if len(df):
        df = add_datetime_columns(df).drop_duplicates("post_uri").reset_index(drop=True)
        if japanese_only:
            df = df[df["is_japanese"]].reset_index(drop=True)
    return df


def search_posts_by_period(query: str, days: int = 7, hours_per_window: int = 24,
                           lang: str | None = "ja", sort: str = "latest",
                           japanese_only: bool = True, end: datetime | None = None,
                           pause: float = 0.7, verbose: bool = True) -> pd.DataFrame:
    """期間を小さな窓に分割して検索し，まとめて DataFrame で返す．

    公開APIは1回の検索で最大100件しか返さないため，
    「直近 days 日を hours_per_window 時間ごとに区切って検索」することで多く集める．
    投稿の多い検索語では hours_per_window を小さく（例: 6 や 3）する．
    """
    end = end or datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    frames = []
    t0 = start
    n_windows = 0
    while t0 < end:
        t1 = min(t0 + timedelta(hours=hours_per_window), end)
        since = t0.strftime("%Y-%m-%dT%H:%M:%SZ")
        until = t1.strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            df = search_posts(query, limit=100, lang=lang, sort=sort, since=since, until=until,
                              japanese_only=japanese_only)
        except RuntimeError as e:
            print(f"  取得失敗（{since}〜{until}）: {e}")
            df = pd.DataFrame()
        n_windows += 1
        if verbose:
            mark = " ←100件に達した可能性（窓を小さくすると増えます）" if len(df) >= 100 else ""
            print(f"  {since} 〜 {until}: {len(df):3d}件{mark}")
        if len(df):
            frames.append(df)
        t0 = t1
        time.sleep(pause)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True).drop_duplicates("post_uri")
    out = out.sort_values("created_at_jst").reset_index(drop=True)
    if verbose:
        print(f"合計 {len(out)} 件（{n_windows} 回の検索，重複除去後）")
    return out


# ----------------------------------------------------------------------
# アカウント（actor）に関する取得
# ----------------------------------------------------------------------

def get_profile(handle: str) -> dict:
    """アカウントのプロフィール（フォロワー数，投稿数など）を取得する．"""
    d = _get("app.bsky.actor.getProfile", {"actor": handle})
    keys = ["did", "handle", "displayName", "description", "followersCount", "followsCount",
            "postsCount", "createdAt"]
    return {k: d.get(k) for k in keys}


def search_actors(query: str, limit: int = 25) -> pd.DataFrame:
    """アカウントを名前で検索する（自治体・報道機関などの公式アカウント探しに）．"""
    d = _get("app.bsky.actor.searchActors", {"q": query, "limit": min(limit, 100)})
    rows = [{"handle": a.get("handle"), "displayName": a.get("displayName"),
             "description": (a.get("description") or "")[:80]} for a in d.get("actors", [])]
    return pd.DataFrame(rows)


def get_author_posts(handle: str, max_posts: int = 200, include_replies: bool = False,
                     include_reposts: bool = False, pause: float = 0.5) -> pd.DataFrame:
    """特定アカウントの投稿を新しい順に最大 max_posts 件取得する．"""
    rows, cursor = [], None
    filt = "posts_with_replies" if include_replies else "posts_no_replies"
    while len(rows) < max_posts:
        params = {"actor": handle, "limit": 100, "filter": filt}
        if cursor:
            params["cursor"] = cursor
        d = _get("app.bsky.feed.getAuthorFeed", params)
        feed = d.get("feed", [])
        for item in feed:
            if not include_reposts and "reason" in item:  # リポストは reason が付く
                continue
            rows.append(post_to_row(item["post"], query=f"@{handle}"))
        cursor = d.get("cursor")
        if not cursor or not feed:
            break
        time.sleep(pause)
    df = pd.DataFrame(rows[:max_posts])
    return add_datetime_columns(df) if len(df) else df


def get_replies(post_uri: str, depth: int = 6) -> pd.DataFrame:
    """ある投稿への返信（スレッド）を平らな表にして返す．"""
    d = _get("app.bsky.feed.getPostThread", {"uri": post_uri, "depth": min(depth, 10)})
    rows = []

    def walk(node, level):
        if not node or "post" not in node:
            return
        for rep in node.get("replies", []) or []:
            if "post" in rep:
                row = post_to_row(rep["post"], query="reply")
                row["depth"] = level
                rows.append(row)
                walk(rep, level + 1)

    walk(d.get("thread"), 1)
    df = pd.DataFrame(rows)
    return add_datetime_columns(df) if len(df) else df


def get_trending_topics(limit: int = 10) -> list[str]:
    """Bluesky が算出しているトレンドの話題を返す（参考用）．"""
    d = _get("app.bsky.unspecced.getTrendingTopics", {"limit": limit})
    return [t.get("topic") for t in d.get("topics", [])]


# ----------------------------------------------------------------------
# 保存・読み込み・匿名化
# ----------------------------------------------------------------------

def save_posts(df: pd.DataFrame, path: str | Path = "data/posts.csv", note: str = "") -> Path:
    """CSV で保存し，取得条件のメモ（JSON）も隣に残す．"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    meta = {
        "saved_at_jst": datetime.now(JST).isoformat(timespec="seconds"),
        "rows": int(len(df)),
        "queries": sorted(df["query"].astype(str).unique().tolist()) if "query" in df else [],
        "created_at_min": str(df["created_at_jst"].min()) if "created_at_jst" in df and len(df) else None,
        "created_at_max": str(df["created_at_jst"].max()) if "created_at_jst" in df and len(df) else None,
        "note": note,
    }
    path.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存しました: {path}（{len(df)}件）")
    return path


def load_posts(path: str | Path = "data/posts.csv") -> pd.DataFrame:
    """save_posts で保存した CSV を読み込む．無ければサンプルデータを読む．"""
    path = Path(path)
    if not path.exists():
        sample = Path(__file__).parent / "sample_data" / "posts_sample.csv"
        print(f"{path} が見つからないので，サンプルデータ {sample.name} を読み込みます．")
        path = sample
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["text"] = df["text"].fillna("").astype(str)
    print(f"読み込み: {path}（{len(df)}件）")
    return add_datetime_columns(df)


def stable_hash(value: str, n: int = 12) -> str:
    """文字列を短いハッシュ値に変換する（同じ入力→同じ出力，元には戻せない）．"""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:n]


def anonymize(df: pd.DataFrame) -> pd.DataFrame:
    """発表・共有用に，投稿者や投稿を特定できる列を落とした表を返す．"""
    drop = [c for c in ["post_uri", "author_handle", "author_name", "image_urls", "image_thumbs",
                        "video_thumb", "external_url"] if c in df.columns]
    return df.drop(columns=drop)


def clean_text(text: str) -> str:
    """URLとメンションを取り除き，空白を整える（テキスト分析の前処理）．"""
    text = _URL_RE.sub(" ", str(text))
    text = _MENTION_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


# ----------------------------------------------------------------------
# 画像のダウンロード
# ----------------------------------------------------------------------

def download_images(df: pd.DataFrame, out_dir: str | Path = "data/images", max_posts: int = 30,
                    size: str = "thumb", all_images: bool = True, max_images: int | None = None,
                    skip_labeled: bool = True, pause: float = 0.3, verbose: bool = True) -> pd.DataFrame:
    """【参考資料】画像付き投稿の画像を保存し，1枚1行の表（post_id, image_index, image_path, alt, width, height, bytes）を返す．

    注意: SNS の画像にはセンシティブな内容（性的・暴力的・不快な画像）が含まれることがある．
          授業の本編では扱わない．使う場合は教員に相談し，少量から確認しながら進めること．
    max_posts    : 画像を取りに行く投稿数の上限（投稿の並び順で先頭から）
    size         : "thumb"（長辺 1000px 程度・数十KB．分析用途はこれで十分）または "fullsize"（最大 2000px・数百KB）
    all_images   : True なら投稿に付いた画像を全部（最大4枚），False なら1枚目だけ
    max_images   : 保存する総枚数の上限（None なら無制限）
    skip_labeled : True なら，モデレーション／自己申告のラベル（porn, sexual, nudity, graphic-media 等）が
                   付いた投稿を除外する．ラベルが無くてもセンシティブな画像はあり得るので過信しない．
    * 画像は webp 形式で届くので JPEG に変換して保存する．ファイル名は {post_id}_{番号}.jpg
    * すでに保存済みのファイルは再取得しない（何度実行してもよい）
    * 一覧を out_dir/images.csv に書き出す（第4回の物体検出で使う）
    """
    from PIL import Image
    from io import BytesIO

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    col = "image_thumbs" if size == "thumb" else "image_urls"
    target = df[df["image_count"].fillna(0) > 0]
    if skip_labeled and "labels" in target.columns:
        labeled = target["labels"].fillna("").astype(str).str.strip() != ""
        if verbose and int(labeled.sum()):
            print(f"  ラベル付き（センシティブの可能性）の投稿 {int(labeled.sum())} 件を除外しました．")
        target = target[~labeled]
    target = target.head(max_posts)
    rows, n_new, n_fail = [], 0, 0
    for _, row in target.iterrows():
        urls = [u for u in str(row.get(col, "") or "").split("|") if u]
        alts = str(row.get("image_alts", "") or "").split("|")
        if not all_images:
            urls = urls[:1]
        for k, url in enumerate(urls, start=1):
            if max_images is not None and len(rows) >= max_images:
                break
            out_path = out_dir / f"{row['post_id']}_{k}.jpg"
            if not out_path.exists():
                try:
                    r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=20)
                    r.raise_for_status()
                    Image.open(BytesIO(r.content)).convert("RGB").save(out_path, "JPEG", quality=90)
                    n_new += 1
                    time.sleep(pause)
                except Exception as e:
                    n_fail += 1
                    if verbose:
                        print(f"  取得失敗: {row['post_id']} 画像{k} {e}")
                    continue
            try:
                with Image.open(out_path) as im:
                    w, h = im.size
            except Exception:
                w = h = 0
            rows.append({"post_id": row["post_id"], "image_index": k, "image_path": str(out_path),
                         "alt": alts[k - 1] if k - 1 < len(alts) else "",
                         "width": w, "height": h, "bytes": out_path.stat().st_size, "size": size})
    images = pd.DataFrame(rows, columns=["post_id", "image_index", "image_path", "alt", "width", "height", "bytes", "size"])
    images.to_csv(out_dir / "images.csv", index=False, encoding="utf-8-sig")
    if verbose:
        mb = images["bytes"].sum() / 1e6 if len(images) else 0
        print(f"画像 {len(images)} 枚（{images['post_id'].nunique()} 投稿，新規 {n_new} 枚，失敗 {n_fail} 枚，合計 {mb:.1f} MB）→ {out_dir}/")
    return images


def show_images(images: pd.DataFrame, n: int = 12, cols: int = 4, caption: str | None = "alt",
                figsize_per: float = 3.0):
    """download_images() の結果を格子状に表示する（Notebook 用）．caption に列名を指定するとその文字列を添える．"""
    import numpy as np
    import matplotlib.pyplot as plt
    from PIL import Image

    sub = images.head(n)
    if not len(sub):
        print("表示する画像がありません．")
        return
    rows_n = (len(sub) + cols - 1) // cols
    fig, axes = plt.subplots(rows_n, cols, figsize=(figsize_per * cols, figsize_per * rows_n))
    axes = list(np.atleast_1d(axes).ravel())
    for ax, (_, r) in zip(axes, sub.iterrows()):
        try:
            ax.imshow(Image.open(r["image_path"]))
        except Exception:
            ax.text(0.5, 0.5, "読み込めません", ha="center")
        title = str(r.get(caption, "") or "")[:28] if caption else ""
        ax.set_title(title or r["post_id"], fontsize=8)
        ax.axis("off")
    for ax in axes[len(sub):]:
        ax.axis("off")
    plt.tight_layout()
    plt.show()


# ----------------------------------------------------------------------
# Jetstream：検索ではなく「いま流れている投稿」を観測する（発展）
# ----------------------------------------------------------------------

def jetstream_collect(seconds: int = 60, lang: str | None = "ja", keyword: str | None = None,
                      max_posts: int = 2000, verbose: bool = True) -> pd.DataFrame:
    """Jetstream（全投稿のリアルタイム配信）を seconds 秒だけ受信し，条件に合う投稿を返す．

    * lang="ja" のとき，投稿の言語タグに ja が含まれるか本文に日本語文字を含むものを残す．
    * keyword を指定すると，本文にその語を含むものだけ残す．
    * 反応数（いいね等）は投稿直後なので含まれない．画像は blob 参照のみ（URL化は省略）．
    """
    from websockets.sync.client import connect  # websockets>=11

    uri = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
    rows, n_all = [], 0
    deadline = time.time() + seconds
    with connect(uri, max_size=4_000_000) as ws:
        while time.time() < deadline and len(rows) < max_posts:
            try:
                frame = ws.recv(timeout=1.0)
            except TimeoutError:
                continue
            msg = json.loads(frame)
            commit = msg.get("commit") or {}
            if commit.get("operation") != "create":
                continue
            rec = commit.get("record") or {}
            text = str(rec.get("text", ""))
            langs = rec.get("langs") or []
            n_all += 1
            if lang and not (lang in langs or (lang == "ja" and _JP_RE.search(text))):
                continue
            if keyword and keyword not in text:
                continue
            did = msg.get("did", "")
            uri_post = f"at://{did}/app.bsky.feed.post/{commit.get('rkey', '')}"
            embed = rec.get("embed") or {}
            n_img = len(embed.get("images", [])) if embed.get("$type") == "app.bsky.embed.images" else 0
            rows.append({
                "post_uri": uri_post, "post_id": stable_hash(uri_post),
                "author_handle": "", "author_id": stable_hash(did), "author_name": "",
                "created_at": rec.get("createdAt"), "text": text,
                "langs": ",".join(langs) if isinstance(langs, list) else str(langs),
                "is_japanese": bool(_JP_RE.search(text)),
                "like_count": 0, "repost_count": 0, "reply_count": 0, "quote_count": 0,
                "image_count": n_img, "image_urls": "", "image_thumbs": "", "image_alts": "",
                "video_thumb": "", "external_url": "", "external_title": "",
                "query": f"jetstream:{keyword or lang or 'all'}",
            })
    if verbose:
        print(f"{seconds}秒間に {n_all} 件の投稿が流れ，条件に合う {len(rows)} 件を集めました．")
    df = pd.DataFrame(rows)
    return add_datetime_columns(df) if len(df) else df


# ----------------------------------------------------------------------
# 日本語テキスト処理（janome）と日本語フォント
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 日本語テキスト処理（janome）
#   前処理は「プリセット」と「個別オプション」で切り替えられる．
#   1. 品詞（大分類）で残す語を選ぶ                  pos
#   2. 品詞の細分類で意味の薄い語を落とす            exclude_detail（非自立動詞「てる」，接尾「れる」，非自立形容詞「ない/ほしい」など）
#   3. 短いひらがなだけの語を落とす                  max_hiragana_len
#   4. ストップワード（stopwords_ja.txt ＋ 追加語）   stopwords / extra_stopwords
# ----------------------------------------------------------------------

STOPWORDS_PATH = Path(__file__).resolve().parent / "stopwords_ja.txt"

# ファイルが無いときのための最小限のストップワード
BUILTIN_STOPWORDS = {
    "する", "ある", "いる", "なる", "できる", "思う", "いう", "言う", "くる", "来る", "いく", "行く", "行う",
    "みる", "見る", "やる", "てる", "れる", "られる", "せる", "ない", "いい", "よい", "すぎる", "しまう",
    "出る", "入る", "くださる", "ください", "ござる", "おる", "ちゃう",
    "こと", "もの", "これ", "それ", "あれ", "ため", "よう", "さん", "ちゃん", "くん",
    "私", "自分", "今日", "今", "人", "的", "そう", "ん", "の", "みたい", "感じ", "とき", "何",
    "http", "https", "www", "com", "jp", "amp", "rt", "[...]", "...", "co",
}


def load_stopwords(path: str | Path = STOPWORDS_PATH) -> set[str]:
    """ストップワードファイル（1行1語，# はコメント）を読み込む．無ければ内蔵の最小セットを返す．"""
    path = Path(path)
    words = set(BUILTIN_STOPWORDS)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                words.add(line)
    return words


DEFAULT_STOPWORDS = load_stopwords()

# 品詞の細分類による除外（(大分類, 細分類1) の組）
EXCLUDE_DETAIL_DEFAULT = {
    ("名詞", "数"), ("名詞", "非自立"), ("名詞", "代名詞"), ("名詞", "接尾"), ("名詞", "特殊"),
    ("動詞", "非自立"),      # てる，ください，すぎる，みる，しまう など（補助動詞）
    ("動詞", "接尾"),        # れる，られる，せる
    ("形容詞", "非自立"),    # ない，ほしい，にくい，やすい
}

# プリセット：用途に応じて切り替える
TOKENIZE_PRESETS = {
    # 標準：内容語（名詞・動詞・形容詞）から意味の薄い語を除く
    "content": dict(pos=("名詞", "動詞", "形容詞"), exclude_detail=EXCLUDE_DETAIL_DEFAULT,
                    max_hiragana_len=2, min_len=2, use_stopwords=True),
    # 名詞だけ：話題（何について語られているか）を見るとき
    "nouns": dict(pos=("名詞",), exclude_detail=EXCLUDE_DETAIL_DEFAULT,
                  max_hiragana_len=2, min_len=2, use_stopwords=True),
    # 名詞＋形容詞：評価・感想の語も見たいとき
    "nouns_adj": dict(pos=("名詞", "形容詞"), exclude_detail=EXCLUDE_DETAIL_DEFAULT,
                      max_hiragana_len=2, min_len=2, use_stopwords=True),
    # 生：ほとんど落とさない（前処理の効果を比べるとき用）
    "raw": dict(pos=("名詞", "動詞", "形容詞", "副詞", "感動詞"), exclude_detail=set(),
                max_hiragana_len=0, min_len=1, use_stopwords=False),
}

_tokenizer = None
_HIRAGANA_ONLY_RE = re.compile(r"^[぀-ゟー]+$")


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from janome.tokenizer import Tokenizer
        _tokenizer = Tokenizer()
    return _tokenizer


def _resolve_options(preset, pos, stopwords, extra_stopwords, min_len, max_hiragana_len, exclude_detail):
    """プリセットの設定に，個別に指定されたオプションを上書きして返す．"""
    if preset not in TOKENIZE_PRESETS:
        raise ValueError(f"preset は {list(TOKENIZE_PRESETS)} のいずれか: {preset}")
    opt = dict(TOKENIZE_PRESETS[preset])
    if pos is not None:
        opt["pos"] = tuple(pos)
    if min_len is not None:
        opt["min_len"] = min_len
    if max_hiragana_len is not None:
        opt["max_hiragana_len"] = max_hiragana_len
    if exclude_detail is not None:
        opt["exclude_detail"] = set(exclude_detail)
    if stopwords is not None:
        opt["stopwords"] = set(stopwords)
    else:
        opt["stopwords"] = set(DEFAULT_STOPWORDS) if opt["use_stopwords"] else set()
    opt["stopwords"] |= set(extra_stopwords or ())
    return opt


def _judge(tok, opt, use_base_form=True):
    """1トークンを残すか判定し，(語, 残すか, 理由) を返す．"""
    p = tok.part_of_speech.split(",")
    w = tok.base_form if (use_base_form and tok.base_form != "*") else tok.surface
    if p[0] not in opt["pos"]:
        return w, False, f"品詞 {p[0]}"
    if (p[0], p[1]) in opt["exclude_detail"]:
        return w, False, f"細分類 {p[0]}-{p[1]}"
    if w.isdigit():
        return w, False, "数字"
    if len(w) < opt["min_len"]:
        return w, False, f"{opt['min_len']}文字未満"
    if opt["max_hiragana_len"] and len(w) <= opt["max_hiragana_len"] and _HIRAGANA_ONLY_RE.match(w):
        return w, False, "短いひらがな"
    if w in opt["stopwords"]:
        return w, False, "ストップワード"
    return w, True, ""


def tokenize(text: str, preset: str = "content", pos=None, stopwords=None, extra_stopwords=(),
             min_len: int | None = None, max_hiragana_len: int | None = None,
             exclude_detail=None, use_base_form: bool = True) -> list[str]:
    """日本語の文を単語（原形）のリストにする．前処理はプリセットとオプションで切り替える．

    preset          : "content"（標準）, "nouns"（名詞のみ）, "nouns_adj", "raw"（ほぼ落とさない）
    pos             : 残す品詞の大分類．例 ("名詞",)
    stopwords       : ストップワード集合を丸ごと差し替える（None ならファイル＋内蔵）
    extra_stopwords : 既定に追加する語（検索語そのものなど）
    min_len         : この文字数未満の語を落とす
    max_hiragana_len: この長さ以下の「ひらがなだけ」の語を落とす（0 で無効）
    exclude_detail  : 落とす品詞細分類の集合．例 {("動詞","非自立")}．set() で無効
    """
    opt = _resolve_options(preset, pos, stopwords, extra_stopwords, min_len, max_hiragana_len, exclude_detail)
    words = []
    for tok in _get_tokenizer().tokenize(clean_text(text)):
        w, keep, _ = _judge(tok, opt, use_base_form)
        if keep:
            words.append(w)
    return words


def explain_tokens(text: str, preset: str = "content", **options) -> pd.DataFrame:
    """1文について，各トークンが「残った／落ちた（理由）」を表で返す（前処理の効果を確かめる用）．"""
    opt = _resolve_options(preset, options.get("pos"), options.get("stopwords"), options.get("extra_stopwords", ()),
                           options.get("min_len"), options.get("max_hiragana_len"), options.get("exclude_detail"))
    rows = []
    for tok in _get_tokenizer().tokenize(clean_text(text)):
        w, keep, why = _judge(tok, opt, options.get("use_base_form", True))
        rows.append({"表層形": tok.surface, "原形": w, "品詞": tok.part_of_speech.replace(",*", ""),
                     "残す": "○" if keep else "", "落とす理由": why})
    return pd.DataFrame(rows)


def japanese_font_path() -> str | None:
    """matplotlib / wordcloud で使える日本語フォントのファイルパスを探す．"""
    from matplotlib import font_manager as fm
    candidates = ["Meiryo", "Yu Gothic", "MS Gothic", "Hiragino Sans", "Hiragino Maru Gothic Pro",
                  "Noto Sans CJK JP", "IPAexGothic", "IPAGothic", "TakaoGothic"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return fm.findfont(fm.FontProperties(family=name))
    return None


def set_japanese_font() -> str | None:
    """matplotlib のグラフで日本語が □ にならないようフォントを設定する．"""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    path = japanese_font_path()
    if path is None:
        print("日本語フォントが見つかりません．pip install matplotlib-fontja を試してください．")
        try:
            import matplotlib_fontja  # noqa: F401  （インポートするだけで有効になる）
            return "matplotlib-fontja"
        except ImportError:
            return None
    name = fm.FontProperties(fname=path).get_name()
    plt.rcParams["font.family"] = name
    plt.rcParams["axes.unicode_minus"] = False
    return name


__all__ = [
    "search_posts", "search_posts_by_period", "search_posts_paged", "get_profile", "search_actors", "get_author_posts",
    "get_replies", "get_trending_topics", "save_posts", "load_posts", "anonymize", "clean_text",
    "download_images", "show_images", "jetstream_collect", "tokenize", "explain_tokens", "load_stopwords",
    "DEFAULT_STOPWORDS", "TOKENIZE_PRESETS", "EXCLUDE_DETAIL_DEFAULT", "STOPWORDS_PATH",
    "japanese_font_path", "set_japanese_font", "posts_to_dataframe", "add_datetime_columns",
    "stable_hash", "login", "login_from_config", "login_status", "logout", "load_config",
    "HOSTS", "CONFIG_PATH",
]
