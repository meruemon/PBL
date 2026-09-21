# -*- coding: utf-8 -*-
"""
download_assets.py ― 画像認識演習で使うデータ・モデルをまとめてダウンロードする

実行方法（Anaconda Prompt，image_recognition フォルダで）:
    python download_assets.py

用意されるもの:
    data/vtest.avi                               歩行者の動画（OpenCV 公式サンプル）
    data/shape_predictor_68_face_landmarks.dat   dlib の顔ランドマークモデル（約100MB）
    data/img/                                    人物写真を置くフォルダ（自分で用意する．下記参照）
    det/yolov5s.onnx                             ※自動では入手できないので README の手順で用意する

data/img/img01.jpg（複数の人が写った写真）と data/img/img02.jpg（顔が正面を向いた写真）は，
自分たちで撮影した写真や，利用条件を確認したフリー素材を置いてください．
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
    if not (BASE / "det" / "yolov5s.onnx").exists():
        print("※ det/yolov5s.onnx がまだありません．README.md の「YOLOv5 モデルの準備」を参照してください．")
    if not any((BASE / "data" / "img").glob("*.jpg")):
        print("※ data/img/ に img01.jpg, img02.jpg（人物写真）を置いてください．")


if __name__ == "__main__":
    main()
