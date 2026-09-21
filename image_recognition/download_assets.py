# -*- coding: utf-8 -*-
"""
download_assets.py ― 画像認識演習で使うデータ・モデルをまとめてダウンロードする

実行方法（Anaconda Prompt，image_recognition フォルダで）:
    python download_assets.py

用意されるもの:
    data/vtest.avi                               歩行者の動画（OpenCV 公式サンプル）
    data/shape_predictor_68_face_landmarks.dat   dlib の顔ランドマークモデル（約100MB）
    data/img/                                    人物写真を置くフォルダ
    det/yolov5s.onnx                             YOLOv5s 学習済みモデル

data/img/img01.jpg，img02.jpg と det/yolov5s.onnx は Dropbox の配布フォルダから手動でダウンロードして置きます．
    https://www.dropbox.com/scl/fo/nkp6an01g3aohmaq47yyo/AC__dvrQ5QQGdlevxi5Chgs?rlkey=i42q8x1dte3cat2ajbx93uub2&st=t7qbp6wb&dl=0
"""
import bz2
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
ASSETS = [
    # (URL, 保存先, bz2圧縮か)
    ("https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/vtest.avi",
     BASE / "data" / "vtest.avi", False),
    ("http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
     BASE / "data" / "shape_predictor_68_face_landmarks.dat", True),
]


def download(url: str, dest: Path, is_bz2: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest.relative_to(BASE)} はすでにあります")
        return
    print(f"[get ] {url}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get("Content-Length", 0))
    tmp = dest.with_suffix(dest.suffix + ".part")
    done = 0
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                sys.stdout.write(f"\r       {done / 1e6:6.1f} / {total / 1e6:6.1f} MB")
                sys.stdout.flush()
    print()
    if is_bz2:
        print("       解凍中…")
        with bz2.open(tmp, "rb") as src, open(dest, "wb") as out:
            out.write(src.read())
        tmp.unlink()
    else:
        tmp.replace(dest)
    print(f"[ok  ] {dest.relative_to(BASE)}")


def main() -> None:
    (BASE / "data" / "img").mkdir(parents=True, exist_ok=True)
    (BASE / "det").mkdir(parents=True, exist_ok=True)
    for url, dest, is_bz2 in ASSETS:
        try:
            download(url, dest, is_bz2)
        except Exception as e:  # ネットワーク障害などで止まらないようにする
            print(f"[fail] {dest.name}: {e}")
    print()
    missing = []
    if not (BASE / "det" / "yolov5s.onnx").exists():
        missing.append("det/yolov5s.onnx")
    for name in ("img01.jpg", "img02.jpg"):
        if not (BASE / "data" / "img" / name).exists():
            missing.append(f"data/img/{name}")
    if missing:
        print("※ 次のファイルは Dropbox の配布フォルダからダウンロードして置いてください:")
        for m in missing:
            print("   -", m)
        print("   https://www.dropbox.com/scl/fo/nkp6an01g3aohmaq47yyo/AC__dvrQ5QQGdlevxi5Chgs?rlkey=i42q8x1dte3cat2ajbx93uub2&st=t7qbp6wb&dl=0")
    else:
        print("すべてのファイルが揃っています．")


if __name__ == "__main__":
    main()
