# Jupyter Notebook と .py スクリプトの使い分け

この講義では Python を **2つの方法** で実行します．

| 方法 | 向いていること | 起動のしかた |
|---|---|---|
| **Jupyter Notebook**（`.ipynb`） | 少しずつ実行して結果を確認する．データの確認，グラフ，試行錯誤 | `jupyter notebook` |
| **スクリプト**（`.py`） | まとまった処理を一気に実行する．カメラを長時間動かす，データを定期的に集める，アプリとして配る | `python file_name.py` |

基礎演習は Notebook が中心です．プロジェクトでは「Notebook で試して，動いたものを `.py` にまとめる」流れになります．

## 1. Jupyter Notebook の基本操作

| 操作 | キー |
|---|---|
| セルを実行して次へ | `Shift + Enter` |
| セルを実行してその場にとどまる | `Ctrl + Enter` |
| 実行中の処理を止める | ツールバーの ■（Interrupt）／ `Esc` → `I` `I` |
| カーネル（Python）を再起動 | メニュー Kernel → Restart |
| 上に／下にセルを追加 | `Esc` → `A` ／ `Esc` → `B` |
| セルを削除 | `Esc` → `D` `D` |
| Markdown セルに変更 | `Esc` → `M` |

- セルの左の `In [ ]` が `In [*]` のときは実行中です．
- 変数は **上から順に実行した結果** が残ります．途中のセルだけ実行してエラーになるときは，上から順に実行し直してください．
- Webカメラのセルは別ウィンドウが開きます．**そのウィンドウを選択して `q` キー** で終了します．閉じないままセルを止めるとカメラがロックされることがあるので，その場合は Kernel → Restart してください．

## 2. `.py` ファイルの作り方

`.py` は「Python コードを書いたテキストファイル」です．Windows の右クリック → 新規作成 ではうまく作れないので，エディタを使います．

- **Spyder**（Anaconda に同梱．Anaconda Navigator から起動）
- **Visual Studio Code**（慣れてきたらおすすめ）
- Jupyter Notebook の File → New → Text File でも作れます

例として `scripts/run_webcam.py` を見てみましょう（画像認識テーマに同梱）．

```python
import cv2

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)   # Webカメラを開く
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):  # q で終了
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```

### `if __name__ == "__main__":` とは

このファイルを **直接実行したときだけ** `main()` を動かすためのおまじないです．
他のファイルから `import` して関数だけ使いたいときに，勝手にカメラが起動しないようにできます．
Notebook では不要ですが，`.py` として配布・再利用するときは必ず付けましょう．

## 3. `.py` の実行

Anaconda Prompt で仮想環境に入り，ファイルのあるフォルダに移動して実行します．

```bash
conda activate pbl2026
cd C:\pbl2026\image_recognition
python scripts/run_webcam.py
```

引数（オプション）を受け取るスクリプトは `--help` で使い方が表示されます．

```bash
python scripts/yolo_detect.py --help
python sns_analysis/scripts/collect_posts.py --help
```

## 4. Notebook から `.py` へ移す手順（プロジェクト向け）

1. Notebook で動作を確認する
2. 必要なセルのコードを1つの `.py` にまとめ，`main()` 関数に入れる
3. 変えたい値（検索語，カメラ番号，しきい値）は `argparse` で引数にするか，ファイル冒頭の定数にする
4. 結果は CSV や画像として **ファイルに保存** する（画面表示だけで終わらせない）
5. `README.md` に「実行方法」を1行書く

`image_recognition/scripts/` と `sns_analysis/scripts/` のスクリプトがそのまま雛形になります．
