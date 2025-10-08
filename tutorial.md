## はじめに

データサイエンス基礎・応用PBL(吉田班)は、チームで画像認識を用いたプロジェクトを考案し、実装する講義です。全3回の講義を通じて、以下の内容を学び、プロジェクトの準備を行います。


1. **画像認識基礎**：PythonでのOpenCV，dlib，MediaPipeの基本と、画像処理の基礎を理解します。
2. **データ分析**：動画像から認識した物体の頻度などを可視化する技法を学びます。
3. **深層学習**：深層学習を用いて画像認識の精度を高める応用方法を学びます。

---

## 事前準備

データ(data.zip)をダウンロードし，jupyter notebook(.ipynb)と同じフォルダにdata.zipの中身を展開します．

[ダウンロードリンク](https://www.dropbox.com/scl/fi/ohgffo9728emr690grjis/data.7z?rlkey=q1uqob3qd4cke93weiylc9liv&st=gk9ngqxh&dl=0)

フォルダ構造は以下の通りです．

```plaintext
.
├── img
│   ├── img01.jpg
│   └── img02.jpg
├── dlib_face_recognition_resnet_model_v1.dat
├── haarcascade_frontalface_alt.xml
├── shape_predictor_68_face_landmarks.dat
├── vtest.avi
├── データ分析.ipynb
├── 画像認識基礎.ipynb
└── 深層学習.ipynb
```

Jupyter notebookは各自の環境で作成して、講義資料を参考にしながら実行結果を確認してください。

---

## 第1回：画像認識基礎

### 講義概要

- **目的**：Pythonを用いてOpenCVとDlibの基本的な使い方を学び、画像処理の基礎を理解します。
- **内容**：
  - 画像および動画の読み込み・表示方法
  - Webカメラからの映像取得
  - 画像内の人物・顔の検出
  - 顔の向きの推定
  - フレームの保存とタイムラプス動画の作成

## 第2回：データ分析

### 講義概要

- **目的**：画像認識結果から得られたデータを分析し、可視化する技法を学びます。
- **内容**：
  - 統計的手法によるデータ分析
  - MatplotlibやPandasを用いたデータの可視化
  - 動画像からの物体頻度の解析

## 第3回：深層学習

### 講義概要

- **目的**：深層学習を用いた高度な画像認識手法を学び、MediaPipeを用いた人間の姿勢推定とノートパソコンでも動作可能なYolov5を用いた物体検出を学びます。
- **内容**：
  - MediaPipeを用いた姿勢推定の実装
  - Yolov5物体検出

---

## Anaconda PromptでのCUI操作

Anaconda Promptは、Pythonやライブラリを正しい環境で実行するための**コマンド入力用ツール**です。
Windowsのスタートメニューから「Anaconda Prompt」を検索して起動します。

### 基本操作

以下の操作を覚えておくと便利です。

| 操作内容          | コマンド例                 | 説明                                |
| ------------- | --------------------- | --------------------------------- |
| カレントディレクトリの確認 | `cd`        | 現在作業しているフォルダを確認する（Windowsでは `cd`） |
| フォルダの移動       | `cd フォルダ名`            | 指定フォルダへ移動する                       |
| 1つ上の階層に戻る     | `cd ..`               | 親ディレクトリに戻る                        |
| ファイル一覧を表示     | `dir`                 | 現在のフォルダ内にあるファイルやフォルダを表示する         |
| Pythonファイルを実行 | `python file_name.py` | Pythonスクリプトを実行する                  |

💡 **補足**：
フォルダ名やファイル名を入力するときに途中まで入力して **Tabキー** を押すと、候補が自動補完されます。
たとえば `cd Desk` と入力して Tabキー を押すと、自動的に `cd Desktop` に補完されます。
長いパス名を入力する際に非常に便利です。

---

## Pythonコードの実行方法

Pythonコードの実行には**2つの方法**があります。

1. **Jupyter Notebook上で実行する方法**
   セル単位でコードを実行できるため、**双方向性が高く、実行結果をその場で確認しやすい**のが特徴です。学習・実験・可視化を行う際に便利です。

2. **.pyファイルとして実行する方法**
   ある程度まとまったコードを動かす場合は、`file_name.py` というスクリプトファイルを作成し、**Anaconda Prompt** などで次のように実行します。

   ```bash
   python file_name.py
   ```

   この方法では、コードを一括実行でき、**アプリケーション的な動作確認や再利用**に適しています。

---

## 実行例：カメラからの画像読み込み

例えば、「画像認識基礎」で扱う**カメラ映像を読み込むプログラム**は以下のように記述します。
`.py`ファイルはWindowsの右クリックメニューからの「新規作成」では正しく作れない場合があるため、**Spyder**（Anacondaに標準で含まれるPython用エディタ）や、慣れてきたら**Visual Studio Code**などのエディタを利用して作成します。  
ここではファイル名を `run_webcam.py` とします。

```python
# -*- coding: utf-8 -*-
"""
Webカメラ映像のリアルタイム表示スクリプト
'q'キーを押すと終了します。
"""

import cv2

def main():
    # Webカメラ映像のキャプチャを開始
    # 0は通常、PCに内蔵されているカメラを指す。外付けカメラを使用する場合は1や2などに変更する
    # cv2.CAP_DSHOWは、Windowsでのパフォーマンス向上のために使用
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("カメラを開くことができません。")
        return

    # キャプチャのプロパティを取得
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # フレームの幅を取得
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) # フレームの高さを取得
    fps = cap.get(cv2.CAP_PROP_FPS)             # フレームレート（FPS）を取得

    # 取得したカメラのプロパティを表示
    print("画像幅:", width)
    print("画像高さ:", height)
    print("FPS:", fps)

    # Webカメラからの映像を連続的に取得し表示するループ
    while cap.isOpened():
        ret, frame = cap.read()  # フレームを1つ取得。retは取得成功フラグ、frameは取得した画像
        
        if not ret:
            print("フレームを取得できません。終了します。")
            break

        # 取得したフレームを表示
        cv2.imshow("Webcam", frame)

        # 'q'キーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("終了キーが押されました。")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
```

---

### コード解説

ポイントは、スクリプトの末尾にある

```python
if __name__ == "__main__":
    main()
```

の部分です。
この構文は、**Pythonスクリプトを直接実行したときだけ処理を実行し、他のファイルからインポートされたときには実行しないようにする**ために使用されます。

これにより、同じコードを**モジュールとして他のプログラムに再利用**しても、意図しない自動実行を防ぐことができます。
Notebook上ではこの構文は必須ではありませんが、スクリプトとして整理・配布する際には非常に重要です。

