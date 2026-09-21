# テーマ② SNS分析：Bluesky の投稿文と画像から「社会の声」を分析する

SNS「Bluesky」の **公開API** から投稿（本文・日時・反応数・画像）を集め，日本語テキストマイニング・可視化・機械学習で分析するプロジェクトを行います．
APIキーやアカウント登録は **不要** です．Python と `requests` だけで取得できます．

## なぜ Bluesky か

- X（旧Twitter）の API は有料化・制限強化が進み，授業で使いにくくなった．
- Bluesky は公開投稿を **ログインなしで** 取得でき，本文・日時・反応数・画像・言語タグを同じ形式で扱える．
- 日本語ユーザが多く，防災・地域・趣味・ニュースなど幅広い話題がある．
- リアルタイムに全投稿が流れる仕組み（Jetstream）もあり，「いま何件流れているか」を観測できる．

## 基礎演習（第2〜4回）

| 回 | Notebook | 内容 |
|---|---|---|
| 第2回 | [01_bluesky_collection.ipynb](01_bluesky_collection.ipynb) | キーワード検索，反応順・ハッシュタグ，期間分割で大量取得，アカウントの投稿，返信スレッド，CSV保存と取得条件の記録，画像ダウンロード，Jetstream |
| 第3回 | [02_text_visualization.ipynb](02_text_visualization.ipynb) | 形態素解析（janome），頻出語，ストップワード，ワードクラウド，日別・時間帯別の投稿数，語の推移，反応数の分布，共起ネットワーク，TF-IDF による特徴語比較 |
| 第4回 | [03_machine_learning.ipynb](03_machine_learning.ipynb) | 教師あり分類（学習・評価・根拠の確認），自分でラベル付けしたデータからの分類器作成と全投稿への適用，K-means クラスタリング，YOLOv5 による投稿画像の物体検出 |

演習は **課題ではありません**．上から順に実行して結果を確認し，検索語やパラメータを変えて挙動を観察してください．
API に接続できない場合は `sample_data/`（授業用の合成データ）が自動で使われます．

## 事前準備

[../docs/01_anaconda_setup.md](../docs/01_anaconda_setup.md) の手順で `pbl2026` 環境を作るだけです．

```bash
conda activate pbl2026
cd sns_analysis
jupyter notebook
```

第4回の画像の物体検出には，画像認識テーマと共通の `../image_recognition/det/yolov5s.onnx` を使います（[../image_recognition/README.md](../image_recognition/README.md) 参照）．無くても他の節は動きます．

## フォルダ構成

```
sns_analysis/
├── 01_bluesky_collection.ipynb / 02_text_visualization.ipynb / 03_machine_learning.ipynb
├── bsky_utils.py                 取得・保存・前処理の共通モジュール（Notebook から import）
├── scripts/
│   └── collect_posts.py          ターミナルから投稿をまとめて収集（プロジェクト用）
├── sample_data/
│   ├── posts_sample.csv          合成サンプル投稿（3話題×122件．実在の投稿ではない）
│   └── labeled_sample.csv        合成サンプルにラベル（4分類）を付けたもの
└── data/                         取得データ置き場（Git 管理外）
    ├── posts.csv / posts.meta.json
    ├── posts_words.csv
    ├── labeling_sheet.csv        自分たちでラベルを付けるシート
    └── images/                   ダウンロードした投稿画像
```

## `bsky_utils.py` の主な関数

| 関数 | 役割 |
|---|---|
| `search_posts(query, limit, sort, lang, since, until)` | キーワード検索（1回最大100件） |
| `search_posts_by_period(query, days, hours_per_window)` | 期間を分割して大量取得（アカウント不要） |
| `search_posts_paged(query, max_posts)` | cursor で続きを連続取得（`login` 後に使う） |
| `search_actors(query)` / `get_profile(handle)` | アカウント検索・プロフィール |
| `get_author_posts(handle, max_posts)` | 特定アカウントの投稿 |
| `get_replies(post_uri)` | 投稿への返信スレッド |
| `jetstream_collect(seconds, keyword)` | リアルタイムに流れる投稿を観測 |
| `save_posts(df, path)` / `load_posts(path)` | CSV 保存（取得条件のメモ付き）・読み込み |
| `download_images(df, out_dir, max_posts)` | 投稿画像の保存 |
| `tokenize(text, pos, stopwords)` | 日本語の形態素解析（原形・品詞フィルタ） |
| `anonymize(df)` | 発表用に投稿者・URL列を落とす |
| `set_japanese_font()` / `japanese_font_path()` | グラフ・ワードクラウドの日本語フォント |
| `login(handle, app_password)` / `logout()` | （任意）アカウントでログインして取得を安定させる／公開ホストに戻す |

## スクリプトの使い方

```bash
cd sns_analysis
python scripts/collect_posts.py --query 防災 --days 7 --window 6 --out data/bosai.csv
python scripts/collect_posts.py --query 防災 --query 観光 --days 3 --window 12 --out data/posts.csv
python scripts/collect_posts.py --author chunichi.bsky.social --max 300 --out data/chunichi.csv
```

## アカウントなし／ありの違い（任意でログインして使える）

授業の演習は **アカウントなし**（公開ホスト）で完結します．プロジェクトで数千件以上を連続取得したいときや，教室で同時にアクセスして 403 が頻発するときは，自分の Bluesky アカウントでログインして使えます（第2回 Notebook の 10 節に例があります）．

| | アカウントなし（既定） | アカウントあり（`login()`） |
|---|---|---|
| 事前準備 | 不要 | Bluesky アカウント＋アプリパスワード |
| 1回の検索 | 最大100件 | 最大100件 |
| 続きの取得（cursor） | 不可 → 期間分割（`search_posts_by_period`） | 可 → `search_posts_paged` |
| アクセス制限 | 送信元ネットワーク単位（教室で共有） | アカウント単位 |
| 取得できる範囲 | 公開投稿・公開プロフィール | 同じ（＋自分のタイムライン等） |

- アプリパスワードは 設定 → プライバシーとセキュリティ → アプリパスワード で発行します．**通常のパスワードは絶対に使わない**．Notebook に書き込まず `getpass` で入力します．
- ログインしても取得できるのは公開投稿だけです．データの扱いのルール（下記）は変わりません．

## 公開APIの制約（2026年9月時点）と対処

- 検索は **1回100件まで**．ページング（続きの取得）は未ログインでは拒否される．→ `since/until` で期間を分割して取得する（`search_posts_by_period`）．
- 同じ場所（学内ネットワーク）から短時間に多数アクセスすると **403** が返ることがある．→ `bsky_utils` が自動で待って再試行する．それでも失敗する窓は，あとで同じ条件で再実行して足す．
- 反応数は **取得した時点の値**．同じ投稿でも時間が経てば変わる．→ 取得日時を必ず記録し，比較は同じ日に同じ条件で行う．
- 検索結果は無作為標本ではない（検索エンジンの並び順や言語判定の影響を受ける）．→ 「何を代表していて，何を代表していないか」を発表で述べる．
- 仕様は変わり得る．→ 変更があれば `bsky_utils.py` だけを直せば Notebook はそのまま動く設計にしている．

## データ倫理（必ず読む）

- 公開投稿でも，特定の個人を晒す・評価する目的で使わない．
- `data/` の中身（投稿一覧・画像）は授業外へ持ち出さない．GitHub にも上げない（`.gitignore` 済み）．
- 発表資料にはハンドル名・投稿URL・画像そのものを原則載せず，集計結果・匿名化した例で示す（`anonymize()`）．
- 投稿から性別・病歴などのセンシティブな属性を推定・分類しない．

## プロジェクトで使える道具の組み合わせ（例）

| やりたいこと | 道具 |
|---|---|
| ある社会課題について，人々の不満・要望を把握する | 期間分割取得 → 形態素解析 → 自分でラベル付け（要望/苦情/情報…）→ 分類器で全投稿に適用 → 割合と推移 |
| 出来事（災害・イベント・発表）の前後で話題がどう変わったか | since/until で期間を分けて取得 → TF-IDF の特徴語比較 → 語の推移グラフ |
| 自治体・企業の発信がどう受け取られているか | `get_author_posts` → 反応数の分析 → `get_replies` で返信の分類 |
| 地域の観光・食の話題を画像から捉える | 画像付き投稿の取得 → YOLO で物体集計 → テキストと結合 |
| 投稿の量やスピードから盛り上がりを測る | Jetstream で一定時間観測 → 語の出現頻度 |
