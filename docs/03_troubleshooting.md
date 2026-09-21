# よくあるエラーと対処

まず確認：**プロンプトの先頭が `(pbl2026)` になっているか**．なっていなければ `conda activate pbl2026`．

## 環境構築

| 症状 | 対処 |
|---|---|
| `conda env create` が途中で止まる／`Solving environment` が終わらない | いったん `Ctrl+C` で止め，[手動での作り方](01_anaconda_setup.md#手動での作り方environmentyml-が失敗したとき)で作る．`conda update -n base conda` で conda を更新してから再試行するのも有効 |
| `dlib` のインストールで失敗する | `dlib` を外して環境を作る（`conda create -n pbl2026 python=3.11` → `pip install -r requirements.txt`）．dlib を使う節は演習では省略してよい（MediaPipe で代替） |
| `pip install` が `Permission denied` / `Access is denied` | Anaconda Prompt を閉じてもう一度開く．OneDrive 同期フォルダ内や日本語パスを避け，`C:\pbl2026` のような場所に置く |
| `pip install` がネットワークエラー | 学内プロキシの場合は別のネットワーク（自宅・テザリング）で行う |
| `conda` コマンドが見つからない | 「Anaconda Prompt」から実行しているか確認（通常のコマンドプロンプトや PowerShell では動かないことがある） |
| `jupyter notebook` を実行してもブラウザが開かない | 表示された `http://localhost:8888/?token=...` の URL をブラウザに貼り付ける |
| Notebook の右上のカーネル名が `pbl2026` と関係ない | Kernel → Change kernel で `Python 3 (ipykernel)` を選ぶ．それでも駄目なら `python -m ipykernel install --user --name pbl2026` を実行して Notebook を開き直す |

## import エラー

| 症状 | 対処 |
|---|---|
| `ModuleNotFoundError: No module named 'cv2'`（や `mediapipe`, `janome` など） | 環境に入っていない．`conda activate pbl2026` してから `jupyter notebook` を起動し直す．入っているのに出るなら `pip install -r requirements.txt` を再実行 |
| `module 'cv2' has no attribute 'HOGDescriptor'`（`CascadeClassifier` も無い） | OpenCV 5 系が入っている．`pip install "opencv-contrib-python<5"` で 4 系に戻す |
| `module 'mediapipe' has no attribute 'solutions'` | 新しい mediapipe（0.10.30 以降・1.x）が入っている．`pip install "mediapipe==0.10.21" "numpy<2"` で戻す |
| `ModuleNotFoundError: No module named 'bsky_utils'` | Notebook を `sns_analysis` フォルダから開いているか確認（`bsky_utils.py` と同じフォルダで開く） |
| `numpy` のバージョン警告が大量に出る | `pip install "numpy<2"` を試す（mediapipe が古い numpy を要求する場合がある） |

## カメラ・ウィンドウ

| 症状 | 対処 |
|---|---|
| `カメラを開けません` | 別のアプリ（Teams, Zoom）がカメラを使っていないか確認．カメラ番号を `0` → `1` に変える．Windows の設定 → プライバシー → カメラ でデスクトップアプリのアクセスを許可 |
| Mac で `cv2.CAP_DSHOW` を付けるとエラー | `cv2.VideoCapture(0)` にする（`CAP_DSHOW` は Windows 専用） |
| ウィンドウが閉じない・固まる | ウィンドウを選択して `q` を押す．反応しなければ Notebook の Kernel → Restart |
| `cv2.imshow` で `The function is not implemented` | `opencv-python-headless` が入っている．`pip uninstall opencv-python-headless opencv-contrib-python-headless` → `pip install "opencv-contrib-python<5"` |
| 動画やカメラが非常に遅い | 検出を `N` フレームごとにする（`num % 10 == 0`），フレームを `cv2.resize` で縮小する，YOLO なら `--every 5` |

## 画像認識テーマ

| 症状 | 対処 |
|---|---|
| `data/img/img01.jpg がありません` | 自分で写真を置く（[image_recognition/README.md](../image_recognition/README.md)）．ファイル名を合わせる |
| `det/yolov5s.onnx がありません` | README の「YOLOv5 モデルの準備」で用意する |
| YOLO の検出結果が何も出ない | `CONF_THRESHOLD` を 0.25 に下げる．入力画像が暗い・小さい場合は改善しないこともある |
| `cv2.dnn.readNet` で `Unsupported ONNX opset` | ONNX 変換時に `--opset 12` を付けて変換し直す |
| dlib の `shape_predictor` が読み込めない | `download_assets.py` の実行が途中で止まっている．`data/shape_predictor_68_face_landmarks.dat` を削除して再実行 |

## SNS分析テーマ

| 症状 | 対処 |
|---|---|
| `設定ファイル bsky_config.ini が無いか未記入です` | `sns_analysis/bsky_config.example.ini` をコピーして `bsky_config.ini` を作り，ハンドル名とアプリパスワードを記入する．Notebook を開いているフォルダ（`sns_analysis`）に置く．書き換えたら Kernel → Restart |
| `設定ファイルの名前が bsky_config.ini.ini になっています` | Windows で拡張子が隠れていて，保存時に `.ini` が二重に付いた．エクスプローラーの「表示 → ファイル名拡張子」をオンにして `bsky_config.ini` に直す（そのままでも読み込むが，直しておく） |
| `ログイン失敗 401: Invalid identifier or password` | ハンドル名（`@` 不要，例 `name.bsky.social`）とアプリパスワード（通常のパスワードではない）を確認．アプリパスワードを発行し直す |
| `Bluesky API にアクセスできませんでした: 403 Forbidden` | ログインできていない（`login_status()` で確認）．ログイン済みなら数十秒待って再実行．どうしても駄目なら `sample_data` で先に進み，後で取得する |
| `認証エラー（401）` がログイン中に出る | ログインの期限切れ後の更新に失敗．Kernel → Restart して再実行 |
| `APIエラー 400: ...` | 検索語が空，`since/until` の形式が不正（`2026-09-01T00:00:00Z` の形式），ハンドル名の誤りなど．メッセージを読む |
| 取得件数が 0 | 検索語が珍しすぎる／英語．`lang=None, japanese_only=False` で試す．`sort="top"` にする |
| グラフの日本語が □（豆腐）になる | `set_japanese_font()` を実行．Mac/Linux でフォントが無ければ `pip install matplotlib-fontja` |
| ワードクラウドで `OSError: cannot open resource` | `japanese_font_path()` が `None`．上と同じくフォントを用意する |
| `jetstream_collect` で `TimeoutError` や接続失敗 | 学内ネットワークが WebSocket を遮断している可能性．別のネットワークで試す．発展内容なので飛ばしてよい |
| 形態素解析が遅い | 数千件なら数十秒．数万件なら `df.sample(5000)` で試してから全体に適用 |
| CSV を Excel で開くと文字化け | `utf-8-sig` で保存しているので通常は化けない．化ける場合は Excel の「データ → テキストから」で UTF-8 を指定 |

## それでも解決しないとき

1. エラーメッセージの **最後の行** をそのままコピーして Web 検索する（英語のままで）．
2. Notebook の Kernel → Restart & Clear Output で最初から実行し直す．
3. 授業中なら教員・TA に，エラーの出たセルと最後の行を見せる．
