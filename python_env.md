事前にAnacondaがインストールされていることを確認してください．Anacondaは，複数のPython環境やライブラリをプロジェクトごとに管理できる仮想環境を作成する機能があります．
これにより，異なるプロジェクトで異なるバージョンのPythonやライブラリを使うことができ，環境の競合を避けることが可能です．以下の手順はAnaconda Prompt上で実行します．

※conda-forgeを利用したライブラリのインストールは時間がかかる場合があるため，十分な時間を確保して実施してください．

## condaのアップデート

まず，conda自体を最新の状態にアップデートします．
```bash
conda update -n base -c defaults conda
```

## conda仮想環境の構築(Pythonバージョンを3.7に設定)

### 方法1:コマンドによる仮想環境の作成
これは，Anacondaを使った仮想環境を作成するコマンドのテンプレートです．
```bash
conda create -n env-name -c channel-name python=3.7
```
* "環境名"には任意の仮想環境名を指定してください．
* "チャンネル名"にはインストール元のチャンネル（通常はconda-forgeなど）を指定します．

実際に，演習で使用するライブラリをインストールするために，Python 3.7を使った仮想環境を作成します．以下のコマンドをそのまま実行してください．
```bash
conda create -n pbl -c conda-forge python=3.7 opencv=4.0.1 dlib=19.22.0 matplotlib=3.5.3 pandas notebook ipykernel ruptures seaborn statsmodels tslearn
```
このコマンドは，"pbl"という仮想環境を作成し，conda-forgeから必要なライブラリを指定のバージョンでインストールします．

| ライブラリ            | 説明                                                                                             |
|-----------------------|------------------------------------------------------------------------------------------------|
| opencv                | リアルタイムの画像およびビデオ処理のためのオープンソースのコンピュータビジョンと機械学習ライブラリ． |
| dlib                  | 機械学習ライブラリ．顔検出やランドマーク検出などのタスクに利用される．|
| statsmodels           | 統計モデルの推定，テストの実行，データの探索のためのクラスと関数を提供する．|
| ruptures              | 時系列データのオフラインの変化点検出に特化したライブラリ．|
| tslearn               | 時系列データの分析のための機械学習ツールを提供する．|
| matplotlib            | ビジュアライゼーションを作成するための総合的な可視化ライブラリ．|
| seaborn               | matplotlibベースのデータ可視化ライブラリ． |
| pandas                | Python上でデータフレームなどのデータ構造を提供するオープンソースのデータ解析と操作のツール．|
| jupyter notebook      | ライブコード，数式，可視化，テキストを含むドキュメントを作成・共有するウェブアプリ．|
| ipykernel             | JupyterのためのIPythonカーネルで，Pythonコードの実行を可能にする．|

### 方法2:~conda_environment.ymlファイルを使った仮想環境の作成~(jupyter notebookが起動しないので検証中)

GitHub(このレポジトリ)に公開されている[conda_environment.yml](conda_environment.yml)ファイルを使って仮想環境を作成する方法です．以下の手順で進めてください．まず，`curl`コマンドを用いてconda_environment.ymlファイルをダウンロードします．
```bash
curl -O https://raw.githubusercontent.com/meruemon/PBL/refs/heads/main/conda_environment.yml
```

conda_environment.ymlファイルはホームフォルダ(自身のユーザ名がついたフォルダ)へ保存されます．
ダウンロードしたconda_environment.ymlファイルを使って仮想環境を作成します．
```bash
conda env create -f conda_environment.yml
```

## 仮想環境の切り替え

作成した仮想環境に切り替えるには以下を実行します．`base`が仮想環境`pbl`に変化することが確認できます．
```bash
(base) C:\Users\ユーザ名> conda activate pbl
(pbl) C:\Users\ユーザ名>
```

仮想環境から抜けて`base`に戻る場合は以下を実行します．
```bash
(pbl) C:\Users\ユーザ名> conda deactivate
(base) C:\Users\ユーザ名>
```

## 仮想環境に追加モジュールをインストール

仮想環境`pbl`に切り替えて，`pip`コマンドでchnagefinderをインストールします．
```bash
(pbl) C:\Users\ユーザ名> pip install changefinder
```
