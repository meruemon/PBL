# テーマ① 画像認識：カメラ映像から「人・顔・物体」を検出して分析する

Python と OpenCV・MediaPipe・YOLOv5 を使い，ノートPC のカメラや動画から物体を検出し，その結果をデータとして分析するアプリケーションを作ります．
昨年度までのプロジェクト例：**ゴミ分類モデル**（缶・瓶・紙・プラを YOLO で識別），**自転車の危険運転検知**（自転車利用者とヘルメット着用を検出）．

## 基礎演習（第2〜4回）

| 回 | Notebook | 内容 |
|---|---|---|
| 第2回 | [01_image_basics.ipynb](01_image_basics.ipynb) | 画像・動画・Webカメラの入出力，フレーム保存，HOG人物検出，Haar顔検出，顔の向き（dlib / MediaPipe），タイムラプス |
| 第3回 | [02_data_analysis.ipynb](02_data_analysis.ipynb) | 検出人数の時系列記録，グラフ，移動平均，変化点検出（PELT），CSV保存，区間集計 |
| 第4回 | [03_deep_learning.ipynb](03_deep_learning.ipynb) | MediaPipe 姿勢推定と関節角度，YOLOv5 物体検出（画像・動画・カメラ），検出結果のCSV記録，独自モデル学習の手順 |

演習は **課題ではありません**．上から順に実行して結果を確認し，値（しきい値，フレーム間隔，検索対象）を変えて挙動を観察してください．

## 事前準備

### 1. 環境構築

[../docs/01_anaconda_setup.md](../docs/01_anaconda_setup.md) の手順で `pbl2026` 環境を作ります．

### 2. 演習データのダウンロード

Anaconda Prompt でこのフォルダに移動し，次を実行します（約110MB）．

```bash
conda activate pbl2026
cd image_recognition
python download_assets.py
```

| ファイル | 内容 | 入手元 |
|---|---|---|
| `data/vtest.avi` | 歩行者の動画 | OpenCV 公式サンプル（自動） |
| `data/shape_predictor_68_face_landmarks.dat` | dlib 顔ランドマークモデル | dlib.net（自動） |
| `data/img/img01.jpg`, `img02.jpg` | 複数の人が写った写真／顔が正面の写真 | **配布フォルダ（Dropbox）** から `data/img/` に置く |
| `det/coco.names` | YOLO の80クラス名 | 同梱 |
| `det/yolov5s.onnx` | YOLOv5s 学習済みモデル（ONNX） | **配布フォルダ（Dropbox）** から `det/` に置く |

### 3. 配布ファイルのダウンロード（第2回までに）

`img01.jpg`，`img02.jpg`，`yolov5s.onnx` は次の Dropbox フォルダで配布します（ログイン不要．右上の「ダウンロード」でまとめて取得できます）．

**https://www.dropbox.com/scl/fo/nkp6an01g3aohmaq47yyo/AC__dvrQ5QQGdlevxi5Chgs?rlkey=i42q8x1dte3cat2ajbx93uub2&st=t7qbp6wb&dl=0**

ダウンロード後，次の場所に置いてください．

```
image_recognition/
├── data/img/img01.jpg
├── data/img/img02.jpg
└── det/yolov5s.onnx
```

配布ファイルは授業内でのみ使用し，再配布しないでください．

### （参考）YOLOv5 モデルを自分で変換する場合

配布ファイルが使えないときは，Google Colab で変換できます．新しいノートブックで次を順に実行し，生成された `yolov5s.onnx` をダウンロードして `det/` に置きます．

```
!git clone https://github.com/ultralytics/yolov5
%cd /content/yolov5
!pip install -r requirements.txt
!wget https://github.com/ultralytics/yolov5/releases/download/v6.1/yolov5s.pt
!python export.py --weights yolov5s.pt --opset 12 --include onnx
```

参考：[YOLOv5 公式リポジトリ](https://github.com/ultralytics/yolov5)，[日本語チュートリアル](https://docs.ultralytics.com/ja/yolov5)，[モデルエクスポートの解説（日本語）](https://docs.ultralytics.com/ja/yolov5/tutorials/model-export)

## フォルダ構成

```
image_recognition/
├── 01_image_basics.ipynb / 02_data_analysis.ipynb / 03_deep_learning.ipynb
├── download_assets.py            演習データのダウンロード
├── det/
│   ├── coco.names                YOLO のクラス名（80種）
│   └── yolov5s.onnx              学習済みモデル（Dropbox で配布）
├── data/                         動画・画像（Git 管理外．img01/02.jpg は Dropbox で配布）
├── scripts/                      Anaconda Prompt から実行する .py
│   ├── run_webcam.py             Webカメラ表示（.py 実行の練習）
│   ├── count_people_webcam.py    Webカメラの人数を時刻付きで CSV 記録
│   ├── yolo_detect.py            YOLO 検出（カメラ・動画・画像，CSV 記録，自作モデル対応）
│   └── hand_gesture.py           MediaPipe による手の21点検出と3D表示
└── advanced/                     発展
    ├── yolo_custom_training.md   独自の物体を検出する YOLO の学習手順（Colab）
    ├── google_image_search.py    Google Custom Search API で学習画像を収集
    └── gaze_estimation.ipynb     視線推定（L2CS-Net，PyTorch が必要）
```

## スクリプトの使い方

```bash
cd image_recognition
python scripts/run_webcam.py                                          # カメラ表示（q で終了）
python scripts/count_people_webcam.py --out data/webcam_people.csv    # 人数を CSV に記録
python scripts/yolo_detect.py --source 0                              # YOLO をカメラで
python scripts/yolo_detect.py --source data/vtest.avi --csv data/yolo.csv --every 5
python scripts/yolo_detect.py --model det/best.onnx --names det/my.names --source 0   # 自作モデル
python scripts/hand_gesture.py                                        # 手の3D骨格（s で座標保存）
```

## プロジェクトで使える道具の組み合わせ（例）

| やりたいこと | 道具 |
|---|---|
| 特定の場所の人通り・混雑を測る | HOG / YOLO の person 検出 → CSV → 時系列・変化点 |
| 独自の物体（ヘルメット，ゴミ，商品）を検出する | 画像収集 → アノテーション → Colab で YOLOv5 学習 → ONNX → `yolo_detect.py` |
| 姿勢・動作を評価する（フォーム，作業，リハビリ） | MediaPipe Pose の関節角度 → 時系列 |
| 手の動き・ジェスチャで操作する | MediaPipe Hands（`hand_gesture.py`） |
| 顔の向き・注意の推定 | MediaPipe Face Mesh / dlib / 視線推定（advanced） |
| （参考・要相談）SNS の投稿画像に何が写っているかを集計する | SNS分析テーマの参考資料で取得した画像 → `yolo_detect.py`（センシティブな画像を含むことがあるため教員に相談） |

## 注意

- Webカメラのセルは別ウィンドウが開きます．**ウィンドウを選択して `q`** で終了します．
- Mac では `cv2.VideoCapture(0, cv2.CAP_DSHOW)` の `cv2.CAP_DSHOW` を外してください．
- 人物を撮影・記録するときは，撮影される人の同意を得て，映像を授業外に持ち出さないでください．
