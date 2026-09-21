# 発展：独自の物体を検出する YOLOv5 モデルを作る（プロジェクト用）

学習済みの `yolov5s.onnx` は COCO の80クラス（人・車・犬・ボトル…）しか検出できません．
「ヘルメット」「缶／瓶／紙／プラ」「自転車利用者」のような **独自のクラス** を検出するには，自分たちで画像を集めて学習させます．
昨年度の2チーム（ゴミ分類，自転車の危険運転検知）はどちらもこの手順で作りました．

学習には GPU が必要なので **Google Colab（無料）** を使い，できたモデルを ONNX に変換してノートPC で動かします．

## 全体の流れと所要時間の目安

| 手順 | 内容 | 目安 |
|---|---|---|
| 1 | 画像を集める（各クラス 200〜500枚） | 1〜2週間（撮影・収集・整理） |
| 2 | アノテーション（矩形とラベルを付ける） | 300枚で 3〜5時間（分担する） |
| 3 | データセットを YOLO 形式に整える | 30分 |
| 4 | Colab で学習 | 30分〜3時間（枚数・エポック数による） |
| 5 | ONNX に変換して手元で動かす | 30分 |

## 1. 画像を集める

- **自分たちで撮影する**（最も確実．使う場面と同じ環境・距離・明るさで撮る．動画で撮って `01_image_basics.ipynb` の「フレーム分割」で切り出すと早い）
- **公開データセットを使う**：[Roboflow Universe](https://universe.roboflow.com/)，[Kaggle](https://www.kaggle.com/datasets)（ライセンスを確認）
- **Web 検索で集める**：`google_image_search.py`（Google Custom Search API のキーが必要．ファイル冒頭の手順参照．学習目的の私的利用でも，発表資料への転載はしない）

コツ：背景・角度・明るさに **多様性** を持たせる．「学習に使った写真と同じ場所でしか動かない」を避けるため．

## 2. アノテーション

ブラウザで使える無料ツールがおすすめです（インストール不要，YOLO 形式で書き出せる）．

| ツール | 特徴 |
|---|---|
| [Roboflow](https://roboflow.com/) | アカウント登録が必要．チームで分担しやすい．データ拡張・分割・YOLOv5 形式エクスポート・Colab 連携まで一貫してできる |
| [makesense.ai](https://www.makesense.ai/) | 登録不要．画像を読み込んで矩形を描き，YOLO 形式で書き出す．軽い作業向き |
| [CVAT](https://www.cvat.ai/) | 本格的．動画のアノテーションに強い |
| LabelImg（pip） | 昨年度まで使用．Python 3.10 以降では動作が不安定なので上のツールを推奨 |

**ラベル付けのルール** をチームで決めてから始めます（どこまで矩形に含めるか，隠れているときはどうするか）．ルールがばらつくと精度が下がります．

## 3. データセットを YOLO 形式に整える

```
dataset/
├── images/
│   ├── train/   img001.jpg ...   （70%）
│   ├── val/     ...              （20%）
│   └── test/    ...              （10%）
├── labels/
│   ├── train/   img001.txt ...   （画像と同名の txt．1行 = 1物体: クラス番号 中心x 中心y 幅 高さ（0〜1に正規化））
│   ├── val/
│   └── test/
└── data.yaml
```

`data.yaml` の例：

```yaml
train: /content/dataset/images/train
val: /content/dataset/images/val
nc: 4
names: ["can", "bottle", "paper", "plastic"]
```

Roboflow を使う場合は「Export → YOLOv5 PyTorch」でこの形式が自動で作られます．`dataset` フォルダを zip にして Google Drive に置きます．

## 4. Google Colab で学習する

Colab で新しいノートブックを作り，**ランタイム → ランタイムのタイプを変更 → GPU（T4）** を選んでから，次を順に実行します．

```python
# 1) YOLOv5 の準備
!git clone https://github.com/ultralytics/yolov5
%cd /content/yolov5
!pip install -r requirements.txt

# 2) Google Drive をマウントしてデータセットを展開
from google.colab import drive
drive.mount('/content/drive')
!unzip -q /content/drive/MyDrive/dataset.zip -d /content/

# 3) 学習（img: 入力サイズ，batch: 一度に処理する枚数，epochs: 繰り返し回数）
!python train.py --img 640 --batch 16 --epochs 100 --data /content/dataset/data.yaml --weights yolov5s.pt --name my_model

# 4) 評価（P/R/mAP を確認）
!python val.py --weights runs/train/my_model/weights/best.pt --data /content/dataset/data.yaml

# 5) ONNX に変換（OpenCV で読めるように opset 12）
!python export.py --weights runs/train/my_model/weights/best.pt --include onnx --opset 12

# 6) ダウンロード
from google.colab import files
files.download('runs/train/my_model/weights/best.onnx')
```

- 学習の途中経過は `runs/train/my_model/results.png` で確認できます（loss が下がり，mAP が上がっていれば順調）．
- 無料枠は連続使用に上限があります．`--epochs` は 50〜100 程度から始め，保存された `best.pt` を Drive にコピーしておきます．
- 評価指標：**P**（適合率：検出したもののうち正解の割合），**R**（再現率：正解のうち検出できた割合），**mAP50**（重なり 50% 以上を正解としたときの平均精度）．

## 5. 手元で動かす

1. `best.onnx` を `image_recognition/det/` に置く
2. クラス名を1行1つ書いたファイル `det/my.names` を作る（`data.yaml` の `names` と同じ順番）
3. 実行

```bash
python scripts/yolo_detect.py --model det/best.onnx --names det/my.names --source 0
python scripts/yolo_detect.py --model det/best.onnx --names det/my.names --source data/test.mp4 --csv data/result.csv
```

Notebook（`03_deep_learning.ipynb`）でも `MODEL` と `NAMES` を書き換えれば同じように使えます．

## うまくいかないとき

| 症状 | 原因と対策 |
|---|---|
| 学習データでは検出できるが，カメラでは検出できない | 環境の違い（背景・距離・明るさ）．実際に使う環境で撮った画像を学習に加える |
| 特定のクラスだけ精度が低い | そのクラスの枚数が少ない／見た目の多様性が大きい（缶の形状など）．枚数を増やす，クラスを分ける |
| 何でも検出してしまう（誤検出） | しきい値を上げる（`--conf 0.6`），「物体なし」の背景画像を学習に加える |
| 学習が終わらない | `--epochs` を減らす，`--img 416` にする，画像枚数を減らして試す |

## 参考

- [YOLOv5 公式（GitHub）](https://github.com/ultralytics/yolov5)
- [Ultralytics ドキュメント（日本語）](https://docs.ultralytics.com/ja/)：カスタムデータでの学習，エクスポート
- 新しい YOLO（YOLOv8/11，`pip install ultralytics`）も同じ流れで使えますが，ONNX の出力形式が異なるため `yolo_detect.py` の後処理を書き換える必要があります．授業では YOLOv5 を標準とします．
