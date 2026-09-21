# 環境構築：Anaconda で演習用の Python 環境を作る

所要時間：20〜30分（ダウンロード量が多いので，学内Wi‑Fi か自宅で余裕をもって行ってください）

## 0. Anaconda とは／なぜ「仮想環境」を作るのか

Anaconda は Python 本体と，データ分析でよく使うライブラリをまとめたパッケージです．
Anaconda には **仮想環境** を作る機能があり，「この授業用のライブラリ一式」を他の授業や研究のものと分けて管理できます．
ライブラリ同士のバージョン衝突を避けられるので，**必ず授業専用の環境 `pbl2026` を作って使います**．

## 1. Anaconda Prompt を開く

Windows のスタートメニューで「Anaconda Prompt」を検索して起動します（Mac はターミナル）．
黒い画面に `(base) C:\Users\ユーザ名>` のように表示されます．`(base)` は「今は base 環境にいる」という意味です．

### 覚えておくと便利なコマンド

| 操作 | コマンド | 説明 |
|---|---|---|
| 今いるフォルダを確認 | `cd` | Windows では引数なしの `cd` で表示（Mac は `pwd`） |
| フォルダの移動 | `cd フォルダ名` | 例：`cd C:\pbl2026` |
| 1つ上のフォルダへ | `cd ..` | |
| ファイル一覧 | `dir`（Mac は `ls`） | |
| Python ファイルを実行 | `python file_name.py` | |

💡 フォルダ名を途中まで入力して **Tab キー** を押すと補完されます．長いパスの入力に便利です．

## 2. 資料のフォルダへ移動する

GitHub からダウンロードして展開したフォルダ（例：`C:\pbl2026`）へ移動します．

```bash
cd C:\pbl2026
dir
```

`environment.yml` と `requirements.txt` が見えていれば OK です．

## 3. 仮想環境を作る（初回のみ）

```bash
conda env create -f environment.yml
```

これで次のことが自動で行われます．

1. Python 3.11 の仮想環境 `pbl2026` を作る
2. `dlib`（顔ランドマーク検出）を conda-forge からインストールする
3. `requirements.txt` に書かれたライブラリを pip でインストールする

途中で `Proceed ([y]/n)?` と聞かれたら `y` を入力して Enter を押します．
数分〜十数分かかります．最後に `done` と表示されれば成功です．

> **失敗したら**：[03_troubleshooting.md](03_troubleshooting.md) の「環境構築」を見てください．
> 多くの場合，次の「手動での作り方」で解決します．

### 手動での作り方（environment.yml が失敗したとき）

```bash
conda create -n pbl2026 -c conda-forge python=3.11 dlib
conda activate pbl2026
pip install -r requirements.txt
```

dlib のインストールだけが失敗する場合は，`dlib` を外して作ってください（dlib を使う節は演習では省略できます）．

```bash
conda create -n pbl2026 python=3.11
conda activate pbl2026
pip install -r requirements.txt
```

## 4. 仮想環境に入る／出る

作った環境に切り替えると，プロンプトの先頭が `(base)` から `(pbl2026)` に変わります．**演習のときは毎回これを実行します**．

```bash
(base) C:\pbl2026> conda activate pbl2026
(pbl2026) C:\pbl2026>
```

元に戻すには：

```bash
(pbl2026) C:\pbl2026> conda deactivate
(base) C:\pbl2026>
```

## 5. 動作確認

環境に入った状態で次を実行し，エラーが出なければ完了です．

```bash
python -c "import cv2, mediapipe, pandas, sklearn, janome, wordcloud; print('OK', cv2.__version__)"
```

dlib も入れた人は：

```bash
python -c "import dlib; print('dlib OK')"
```

## 6. Jupyter Notebook を起動する

```bash
conda activate pbl2026
cd C:\pbl2026
jupyter notebook
```

ブラウザが自動で開き，フォルダ一覧が表示されます．`image_recognition` または `sns_analysis` を開いて，`01_...ipynb` をクリックしてください．
終了するときは Anaconda Prompt で `Ctrl + C` を押します．

## 7. テーマ別の追加準備

- **画像認識**：`image_recognition/README.md` の「事前準備」（`download_assets.py` の実行と Dropbox 配布ファイルの配置）．
- **SNS分析**：Bluesky の無料アカウントを作り，アプリパスワードを発行して `sns_analysis/bsky_config.ini` に記入する（`sns_analysis/README.md` の「事前準備」）．

## 8. インストールされる主なライブラリ

| ライブラリ | 役割 | テーマ |
|---|---|---|
| notebook / ipykernel | Jupyter Notebook 本体 | 共通 |
| numpy / pandas | 数値配列・表データ | 共通 |
| matplotlib / seaborn | グラフ描画 | 共通 |
| scikit-learn | 機械学習（分類・クラスタリング） | 共通 |
| requests | Web API へのアクセス | 共通 |
| Pillow | 画像ファイルの読み書き | 共通 |
| opencv-contrib-python | 画像・動画処理，古典的な検出器，DNN 推論 | 画像認識 |
| mediapipe | 顔メッシュ・姿勢・手の検出 | 画像認識 |
| dlib | 顔検出と68点ランドマーク | 画像認識（任意） |
| ruptures | 時系列の変化点検出 | 画像認識 |
| janome | 日本語形態素解析 | SNS分析 |
| wordcloud | ワードクラウド | SNS分析 |
| networkx | ネットワーク（共起）の描画 | SNS分析 |
| websockets | Bluesky Jetstream（リアルタイム投稿） | SNS分析 |
