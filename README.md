# データサイエンス基礎・応用PBL（吉田班）

関西大学 システム理工学部 ／ データサイエンス基礎PBL（2年）・応用PBL（3年）合同 ／ 担当：吉田 壮

チームで **社会課題を解決するデータサイエンス・プロジェクト** を企画し，実装し，発表する講義です．
吉田班では次の2つのテーマから選び，混合チーム（5名）でプロジェクトを進めます．

| テーマ | 何ができるようになるか | 主な道具 |
|---|---|---|
| **① 画像認識** | カメラ映像から人・顔・物体を検出し，数えて，分析するアプリを作る | OpenCV，MediaPipe，YOLOv5 |
| **② SNS分析** | SNS（Bluesky）から投稿文と画像を集め，話題・反応・時間変化を分析する | Bluesky API，janome，scikit-learn，YOLOv5 |

どちらのテーマも **「データ取得 → 加工・可視化 → 機械学習・深層学習」** の3回の基礎演習で道具を身につけ，その後の10回でプロジェクトを行います．
2つのテーマは組み合わせても構いません（例：SNSで見つけた困りごとの現場をカメラで計測する）．
※ SNS の投稿画像のダウンロードは，センシティブな画像を含むことがあるため本編では扱わず，参考資料としています（`sns_analysis/reference/`）．

---

## スケジュール

| 回 | 内容 | 資料 |
|---|---|---|
| 第1回 | ガイダンス，テーマ説明，グループ分け | ガイダンス資料 |
| 第2回 | 基礎演習① **データ取得** | [画像認識](image_recognition/01_image_basics.ipynb) / [SNS分析](sns_analysis/01_bluesky_collection.ipynb) |
| 第3回 | 基礎演習② **データ加工・ビジュアライゼーション** | [画像認識](image_recognition/02_data_analysis.ipynb) / [SNS分析](sns_analysis/02_text_visualization.ipynb) |
| 第4回 | 基礎演習③ **機械学習・深層学習**，グループ決定 | [画像認識](image_recognition/03_deep_learning.ipynb) / [SNS分析](sns_analysis/03_machine_learning.ipynb) |
| 第5〜6回 | プロジェクト考案（ディスカッション，企画シート作成） | [企画シート](project/planning_sheet.md) |
| 第7〜12回 | プロジェクト制作 | [プロジェクトガイド](docs/04_project_guide.md) |
| 第13回 | 発表練習 | [発表テンプレート](project/presentation_template.md) |
| 第14回 | 合同プレゼンテーション会 | |

---

## はじめかた（3ステップ）

### 1. この資料を手元に置く

GitHub の緑の **Code** ボタン → **Download ZIP** でダウンロードし，展開します（`git` が使えるなら `git clone`）．
展開先は **日本語や空白を含まないパス** が無難です（例：`C:\pbl2026`）．

### 2. Python 環境を作る（初回のみ，20〜30分）

Anaconda がインストールされていることを確認し，**Anaconda Prompt** を開いて次を実行します．
詳しい手順とトラブル対処は [docs/01_anaconda_setup.md](docs/01_anaconda_setup.md) を見てください．

```bash
cd C:\pbl2026
conda env create -f environment.yml
conda activate pbl2026
```

### 3. Jupyter Notebook を起動して演習を開く

```bash
conda activate pbl2026
jupyter notebook
```

ブラウザが開くので，`image_recognition` または `sns_analysis` フォルダの `01_...ipynb` を開き，上から順にセルを実行します．
Notebook と `.py` スクリプトの使い分けは [docs/02_jupyter_and_python.md](docs/02_jupyter_and_python.md) を見てください．

> **画像認識テーマの人へ**：演習用の動画・モデルが別途必要です．[image_recognition/README.md](image_recognition/README.md) の「事前準備」（自動ダウンロードと Dropbox 配布ファイル）を先に済ませてください．
> **SNS分析テーマの人へ**：無料の Bluesky アカウントと「アプリパスワード」が必要です．[sns_analysis/README.md](sns_analysis/README.md) の「事前準備」に従って `bsky_config.ini` を作ってから始めてください（有料の API キー申請はありません）．

---

## フォルダ構成

```
PBL2026/
├── README.md                     ← このファイル
├── environment.yml               ← conda 環境定義（両テーマ共通）
├── requirements.txt              ← pip でインストールするライブラリ
├── docs/
│   ├── 01_anaconda_setup.md      ← 環境構築（Anaconda Prompt の使い方から）
│   ├── 02_jupyter_and_python.md  ← Notebook と .py の使い分け
│   ├── 03_troubleshooting.md     ← よくあるエラーと対処
│   └── 04_project_guide.md       ← プロジェクトの進め方（第5回〜）
├── image_recognition/            ← テーマ① 画像認識
│   ├── README.md
│   ├── 01_image_basics.ipynb     ← 第2回：画像・動画・カメラ，人物/顔検出
│   ├── 02_data_analysis.ipynb    ← 第3回：検出結果の時系列分析
│   ├── 03_deep_learning.ipynb    ← 第4回：MediaPipe 姿勢推定，YOLOv5 物体検出
│   ├── download_assets.py        ← 演習データのダウンロード
│   ├── scripts/                  ← ターミナルから実行する .py（カメラ表示，人数記録，YOLO検出，手の3D表示）
│   ├── advanced/                 ← 発展（独自YOLOの学習手順，Google画像収集，視線推定）
│   ├── det/                      ← YOLO のクラス名・モデル置き場
│   └── data/                     ← 画像・動画置き場（Git管理外）
├── sns_analysis/                 ← テーマ② SNS分析
│   ├── README.md
│   ├── bsky_utils.py             ← Bluesky 取得・前処理の共通モジュール（設定ファイルから自動ログイン）
│   ├── bsky_config.example.ini   ← アカウント設定の雛形（コピーして bsky_config.ini を作る）
│   ├── 01_bluesky_collection.ipynb   ← 第2回：投稿・アカウント・返信・画像の取得
│   ├── 02_text_visualization.ipynb   ← 第3回：形態素解析，頻出語，時系列，共起，TF-IDF
│   ├── 03_machine_learning.ipynb     ← 第4回：分類器の学習・適用，クラスタリング（参考：画像の物体検出）
│   ├── reference/                ← 参考資料（投稿画像のダウンロード．本編では扱わない）
│   ├── scripts/collect_posts.py  ← ターミナルから投稿をまとめて収集
│   ├── sample_data/              ← API に接続できないときの合成サンプル
│   └── data/                     ← 取得したデータ置き場（Git管理外）
└── project/
    ├── planning_sheet.md         ← 企画シート（第5〜6回）
    └── presentation_template.md  ← 最終発表の構成テンプレート
```

---

## 昨年度までのプロジェクト例

- ゴミ分類モデル（缶・瓶・紙・プラスチックを YOLO で識別し，分別を支援）
- 自転車の危険運転検知システム（自転車利用者とヘルメット着用を検出し，未着用が多い場所・時間帯を可視化）
- 空席認識・状況把握システム，顔認識を用いた授業集中度の測定，AIカメラを用いたセルフレジ，視線追跡システム

---

## ライセンス・注意

- この教材のコードは教育目的で自由に利用・改変できます．
- 取得したSNSデータ・撮影した映像は **授業内でのみ利用** し，再配布しないでください．発表資料に個人が特定できる情報を載せないでください．
- 外部ライブラリ・学習済みモデル（OpenCV，dlib，MediaPipe，YOLOv5 など）はそれぞれのライセンスに従います．
