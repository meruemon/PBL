事前にAnacondaがインストールされていることを確認してください．以下の手順はAnaconda Prompt上で実行します．

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
このコマンドは，"pbl"という仮想環境を作成し，conda-forgeから必要なライブラリ（opencv, dlib, matplotlib, pandas, jupyter notebook, ipykernel, ruptures）を指定のバージョンでインストールします．

### 方法2:conda_environment.ymlファイルを使った仮想環境の作成

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

## 仮想環境に追加ライブラリをインストール

仮想環境`pbl`に切り替えて，`pip`コマンドでchnagefinderをインストールします．
```bash
(pbl) C:\Users\ユーザ名> pip install changefinder
```
