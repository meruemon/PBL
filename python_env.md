事前にAnacondaがインストールされていることを確認してください．以下の手順はAnaconda Prompt上で実行します．

※conda-forgeを利用したライブラリのインストールは時間がかかる場合があるため，十分な時間を確保して実施してください．

## condaのアップデート

まず，conda自体を最新の状態にアップデートします．
```bash
(base) C:\Users\ユーザ名> conda update -n base -c defaults conda
```

## conda仮想環境の構築(Pythonバージョンを3.7に設定)

これは，Anacondaを使った仮想環境を作成するコマンドです．
```bash
(base) C:\Users\ユーザ名> conda create -n env-name -c channel-name python=3.7
```
* "環境名"には任意の仮想環境名を指定してください．
* "チャンネル名"にはインストール元のチャンネル（通常はconda-forgeなど）を指定します．

実際に，講義で使用するライブラリをインストールするために，Python 3.7を使った仮想環境を作成します．以下のコマンドをそのまま実行してください．
```bash
(base) C:\Users\ユーザ名> conda create -n pbl -c conda-forge python=3.7 opencv=4.0.1 dlib=19.22.0 matplotlib=3.5.3
```
このコマンドは，"pbl"という仮想環境を作成し，conda-forgeから必要なライブラリ（opencv, dlib, matplotlib）を指定のバージョンでインストールします．

## 仮想環境の切り替え

作成した仮想環境に切り替えるには以下を実行します．
```bash
(base) C:\Users\ユーザ名> conda activate pbl
(pbl) C:\Users\ユーザ名>
```

仮想環境から抜けて(base)に戻る場合は以下を実行します．
```bash
(pbl) C:\Users\ユーザ名> conda deactivate
(base) C:\Users\ユーザ名>
```

作成した仮想環境にJupyter Notebookとipykernelをインストールします．
```bash
(pbl) C:\Users\ユーザ名> conda install -c conda-forge notebook ipykernel
```
