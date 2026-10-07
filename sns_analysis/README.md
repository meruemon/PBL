# テーマ② SNS分析：Bluesky の投稿文と画像から「社会の声」を分析する

SNS「Bluesky」の API から投稿（本文・日時・反応数・画像）を集め，日本語テキストマイニング・可視化・機械学習で分析するプロジェクトを行います．
有料の API キー申請は不要です．**無料の Bluesky アカウント**と「アプリパスワード」を設定ファイルに書くだけで，Python と `requests` で取得できます．

## なぜ Bluesky か

- X（旧Twitter）の API は有料化・制限強化が進み，授業で使いにくくなった．
- Bluesky は無料アカウントで公開投稿を取得でき，本文・日時・反応数・画像・言語タグを同じ形式で扱える．
- 日本語ユーザが多く，防災・地域・趣味・ニュースなど幅広い話題がある．
- リアルタイムに全投稿が流れる仕組み（Jetstream）もあり，「いま何件流れているか」を観測できる．

## 基礎演習（第2〜4回）

| 回 | Notebook | 内容 |
|---|---|---|
| 第2回 | [01_bluesky_collection.ipynb](01_bluesky_collection.ipynb) | アカウント設定，キーワード検索，反応順・ハッシュタグ，cursor・期間分割で大量取得，アカウントの投稿，返信スレッド，CSV保存と取得条件の記録，画像付き投稿の割合，Jetstream |
| 第3回 | [02_text_visualization.ipynb](02_text_visualization.ipynb) | 形態素解析（janome），前処理の切り替え（品詞・細分類・ひらがな・ストップワードのプリセット），頻出語，ワードクラウド，日別・時間帯別の投稿数，語の推移，反応数の分布，共起ネットワーク，TF-IDF による特徴語比較 |
| 第4回 | [03_machine_learning.ipynb](03_machine_learning.ipynb) | 教師あり分類（学習・評価・根拠の確認），自分でラベル付けしたデータからの分類器作成と全投稿への適用，K-means クラスタリング，発展：学習済みモデルによる感情分析（日本語・多言語） |
| 発展 | [04_english_analysis.ipynb](04_english_analysis.ipynb) | 英語圏の投稿の分析（世界情勢）：言語指定の検索，トレンド，英語の前処理（`tokenize_en`），頻出語・TF-IDF，UTC での時間変化，国・地域の言及数，同じ話題の日英比較，報道機関の投稿 |

演習は **課題ではありません**．上から順に実行して結果を確認し，検索語やパラメータを変えて挙動を観察してください．
API に接続できない場合は `sample_data/`（授業用の合成データ．日本語 `posts_sample.csv`，英語 `posts_sample_en.csv`）が自動で使われます．

### 参考資料（本編では扱わない）

| Notebook | 内容 |
|---|---|
| [reference/image_download.ipynb](reference/image_download.ipynb) | 投稿画像のダウンロード（複数枚，代替テキスト，縮小版と原寸，一覧表示，`scripts/download_images.py`） |

> **SNS の画像にはセンシティブな内容（性的・暴力的・不快な画像）が含まれることが分かっています．** そのため画像のダウンロードは授業の本編から外し，参考資料としています．画像を扱うプロジェクトを行う場合は教員に相談し，参考資料の注意事項（モデレーション／自己申告ラベル付き投稿の除外，少量からの目視確認，公式アカウントへの限定，再配布禁止）に従ってください．

## 事前準備

### 1. Python 環境

[../docs/01_anaconda_setup.md](../docs/01_anaconda_setup.md) の手順で `pbl2026` 環境を作ります．

### 2. Bluesky アカウントと設定ファイル（第2回までに）

1. アカウントを持っていなければ https://bsky.app で作成する（無料．メールアドレスが必要）．
2. Bluesky の **設定 → プライバシーとセキュリティ → アプリパスワード → アプリパスワードを追加** で発行し，表示された `xxxx-xxxx-xxxx-xxxx` を控える（この画面でしか表示されない）．**通常のログインパスワードは使わない**．
3. `sns_analysis/bsky_config.example.ini` をコピーして `sns_analysis/bsky_config.ini` を作り，`handle` と `app_password` を自分のものに書き換える．

```ini
[bluesky]
handle = your-name.bsky.social
app_password = xxxx-xxxx-xxxx-xxxx
```

`bsky_config.ini` は `.gitignore` に登録済みです（GitHub に上がりません）．他人に見せない・共有しないでください．
Windows でファイル名が `bsky_config.ini.ini` や `bsky_config.ini.txt` になってしまう場合は，エクスプローラーの「表示 → ファイル名拡張子」をオンにして直してください．
Notebook や scripts を実行すると，`bsky_utils` が最初の API 呼び出し時に自動でログインします．

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
├── 04_english_analysis.ipynb     発展：英語圏の投稿の分析（世界情勢）
├── bsky_utils.py                 取得・保存・前処理の共通モジュール（Notebook から import）
├── stopwords_ja.txt              日本語ストップワード（1行1語．自由に追加・削除）
├── stopwords_en.txt              英語ストップワード（同上）
├── bsky_config.example.ini       アカウント設定の雛形（コピーして bsky_config.ini を作る）
├── bsky_config.ini               自分のハンドル名とアプリパスワード（Git 管理外）
├── reference/
│   └── image_download.ipynb      【参考】投稿画像のダウンロード（本編では扱わない）
├── scripts/
│   ├── collect_posts.py          ターミナルから投稿をまとめて収集（プロジェクト用）
│   └── download_images.py        【参考】取得済み CSV から画像をまとめて保存
├── sample_data/
│   ├── posts_sample.csv          合成サンプル投稿（3話題×122件．実在の投稿ではない）
│   ├── posts_sample_en.csv       英語の合成サンプル投稿（2話題×120件．実在の投稿ではない）
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
| `login_status()` | ログインできているかを表示 |
| `search_posts(query, limit, sort, lang, since, until)` | キーワード検索（1回最大100件） |
| `search_posts_paged(query, max_posts, since, until)` | cursor で続きを連続取得（標準の大量取得．要ログイン） |
| `search_posts_by_period(query, days, hours_per_window)` | 期間を分割して取得（ログインなしでも動く） |
| `search_actors(query)` / `get_profile(handle)` | アカウント検索・プロフィール |
| `get_author_posts(handle, max_posts)` | 特定アカウントの投稿 |
| `get_replies(post_uri)` | 投稿への返信スレッド |
| `jetstream_collect(seconds, keyword)` | リアルタイムに流れる投稿を観測 |
| `save_posts(df, path)` / `load_posts(path)` | CSV 保存（取得条件のメモ付き）・読み込み |
| `download_images(df, out_dir, max_posts, size, all_images, skip_labeled)` | 【参考】投稿画像の保存（最大4枚／投稿，thumb / fullsize，一覧 `images.csv`）．ラベル付き投稿は既定で除外 |
| `show_images(images, n, cols, caption)` | 【参考】保存した画像を格子状に表示 |
| `tokenize(text, preset, extra_stopwords, ...)` | 日本語の形態素解析．前処理はプリセット（`content` / `nouns` / `nouns_adj` / `raw`）と個別オプション（品詞，細分類除外，短いひらがな，ストップワード）で切り替え |
| `explain_tokens(text, preset, ...)` | 1文の各語が残ったか・落ちた理由を表で表示（前処理の確認用） |
| `tokenize_en(text, extra_stopwords, keep_hashtags)` | 英語の前処理（小文字化・記号除去・`stopwords_en.txt`） |
| `tokenize_any(text, ...)` | 日本語文字を含めば `tokenize`，含まなければ `tokenize_en`（日英混在データ用） |
| `load_stopwords()` / `STOPWORDS_PATH` | `stopwords_ja.txt`（1行1語）を読み直す |
| `anonymize(df)` | 発表用に投稿者・URL列を落とす |
| `set_japanese_font()` / `japanese_font_path()` | グラフ・ワードクラウドの日本語フォント |
| `login(handle, app_password)` / `login_from_config()` / `logout()` | 手動ログイン／設定ファイルからログイン／公開ホストに戻す（通常は自動なので不要） |

## スクリプトの使い方

```bash
cd sns_analysis
python scripts/collect_posts.py --query 防災 --max 1000 --out data/bosai.csv
python scripts/collect_posts.py --query 防災 --query 観光 --max 500 --out data/posts.csv
python scripts/collect_posts.py --query 防災 --method period --days 7 --window 6 --out data/bosai.csv
python scripts/collect_posts.py --author chunichi.bsky.social --max 300 --out data/chunichi.csv
python scripts/download_images.py --csv data/posts.csv --out data/images --max-posts 100          # 画像をまとめて保存
python scripts/download_images.py --csv data/posts.csv --query 観光 --size fullsize --max-posts 50
```

## ログインなし／ありの違い

`bsky_config.ini` が無い，またはログインに失敗したときは，`bsky_utils` は **ログインなしの公開ホスト**にフォールバックします（その旨を表示します）．ただし公開ホストには次の制約があるため，授業では **アカウントでログインして使うのを標準** とします．

| | ログインなし（公開ホスト） | ログインあり（標準） |
|---|---|---|
| 事前準備 | 不要 | 無料アカウント＋アプリパスワード（`bsky_config.ini`） |
| アクセス先 | `api.bsky.app` | 自分のサーバ `bsky.social`（公開データに中継） |
| 1回の検索 | 最大100件 | 最大100件 |
| 続きの取得（cursor） | 拒否される（403）→ `search_posts_by_period` で期間分割 | 可 → `search_posts_paged` で数千件まで |
| アクセス制限 | 送信元ネットワーク単位．**学内から拒否されることがある** | アカウント単位．教室で同時に使っても影響を受けにくい |
| 取得できる範囲 | 公開投稿・公開プロフィール | 同じ（＋自分のタイムライン等） |
| 責任 | ― | 自分のアカウントでのアクセスとして記録される．利用規約を守る |

- ログインしても取得できるのは公開投稿だけです．データの扱いのルール（下記）は変わりません．
- アプリパスワードは自分だけの秘密です．Notebook やコードに書かない．漏れたと思ったら Bluesky の設定画面で削除して発行し直す．

## API の制約（2026年9月時点）と対処

- 検索は **1回100件まで**．続きは cursor で取得する（`search_posts_paged`）．ログインなしでは cursor が拒否される．
- 短時間に多数アクセスすると **429 / 403** が返ることがある．→ `bsky_utils` が自動で待って再試行する．ログインの期限（約2時間）が切れたときも自動で更新する．
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
| 世界の出来事（選挙・紛争・気候・国際スポーツ）への反応を，日本と世界で比べる | `04_english_analysis.ipynb`：英語で収集 → `tokenize_en` → 国・地域の言及数，UTC の時間変化 → 日本語の同じ話題と比較（多言語の感情分析モデルで同じ基準に） |
| 投稿がポジティブかネガティブか | 学習済みモデル（03 の 4 節） |
