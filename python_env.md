## condaのアップデート

```bash
(base) C:\Users\ユーザ名> conda update -n base -c defaults conda
```

## conda仮想環境の構築(使用するPythonのバージョンを3.8にする)

```bash
(base) C:\Users\ユーザ名> conda create -n env-name -c channel-name python=3.7
```

"env-name"には任意の環境名を，"channel-name"にはインストール元のchannel名を入れる．
例えば，

```bash
(base) C:\Users\ユーザ名> conda create -n pbl -c conda-forge python=3.7 opencv=4.0.1 dlib=19.22.0 matplotlib=3.5.3
```

とすると，"pbl"という名前の仮想環境を作り，必要なライブラリをconda-forgeからインストールする．

```bash
(base) C:\Users\ユーザ名> conda activate pbl
```

```bash
(pbl) C:\Users\ユーザ名> conda install -c conda-forge jupyterlab
```
