## はじめに

データサイエンス基礎・応用PBL(吉田班)は、チームで画像認識を用いたプロジェクトを考案し、実装する講義です。全3回の講義を通じて、以下の内容を学び、プロジェクトの準備を行います。


1. **画像認識基礎**：PythonでのOpenCVとDlibの基本と、画像処理の基礎を理解します。
2. **データ分析**：動画像から認識した物体の頻度などを可視化する技法を学びます。
3. **深層学習**：深層学習を用いて画像認識の精度を高める応用方法を学びます。

## 事前準備

データ(data.zip)をダウンロードし，jupyter notebook(.ipynb)と同じフォルダにdata.zipの中身を展開します．

[ダウンロードリンク](https://www.dropbox.com/scl/fi/3pqqorq6hv0dhbvw258ne/data.zip?rlkey=mgtvmqw9ol5phn5erqy97jrs5&st=deahdzem&dl=0)

フォルダ構造は以下の通りです．

```plaintext
.
├── det
│   ├── MobileNetSSD_deploy.caffemodel
│   └── MobileNetSSD_deploy.prototxt
├── img
│   ├── img01.jpg
│   └── img02.jpg
├── pose
│   ├── coco
│   │   ├── pose_deploy_linevec.prototxt
│   │   └── pose_iter_440000.caffemodel
│   └── mpi
│       ├── pose_deploy_linevec.prototxt
│       ├── pose_deploy_linevec_faster_4_stages.prototxt
│       └── pose_iter_160000.caffemodel
├── dlib_face_recognition_resnet_model_v1.dat
├── haarcascade_frontalface_alt.xml
├── shape_predictor_68_face_landmarks.dat
├── vtest.avi
├── データ分析.ipynb
├── 画像認識基礎.ipynb
└── 深層学習.ipynb
```

## 第1回：画像認識基礎

### 講義概要

- **目的**：Pythonを用いてOpenCVとDlibの基本的な使い方を学び、画像処理の基礎を理解する。
- **内容**：
  - 画像および動画の読み込み・表示方法
  - Webカメラからの映像取得
  - 画像内の人物・顔の検出
  - 顔の向きの推定
  - フレームの保存とタイムラプス動画の作成

## 第2回：データ分析

### 講義概要

- **目的**：画像認識結果から得られたデータを分析し、可視化する技法を学ぶ。
- **内容**：
  - 統計的手法によるデータ分析
  - MatplotlibやPandasを用いたデータの可視化
  - 動画像からの物体頻度の解析

## 第3回：深層学習

### 講義概要

**目的**：深層学習を用いた高度な画像認識手法を学び、ノートパソコンでも動作可能な軽量モデルであるMobileNetSSDと、人間の姿勢推定を行うOpenPoseを理解します。
**内容**：
- 軽量な深層学習モデルMobileNetSSDを用いた物体検出
- OpenPoseを用いた姿勢推定の実装
