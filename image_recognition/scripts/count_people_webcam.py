# -*- coding: utf-8 -*-
"""
count_people_webcam.py ― Webカメラの映像から人物（HOG）を検出し，人数を時刻とともにCSVに記録する

使い方（Anaconda Prompt，image_recognition フォルダで）:
    python scripts/count_people_webcam.py --out data/webcam_people.csv
    python scripts/count_people_webcam.py --camera 1 --every 5      # 外付けカメラ，5フレームごとに検出

'q' キーで終了．終了後，記録したCSVを 02_data_analysis.ipynb の手順で分析できる．
"""
import argparse
import csv
import time
from pathlib import Path

import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--out", default="data/webcam_people.csv")
    ap.add_argument("--every", type=int, default=3, help="Nフレームごとに検出する")
    args = ap.parse_args()

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)   # Mac: cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("カメラを開けません")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    f = open(args.out, "w", newline="", encoding="utf-8-sig")
    writer = csv.writer(f)
    writer.writerow(["time", "people"])

    t0 = time.time()
    n = 0
    human = []
    print("記録中… 'q' で終了")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if n % args.every == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            human, _ = hog.detectMultiScale(gray, winStride=(8, 8), padding=(32, 32), scale=1.05)
            writer.writerow([round(time.time() - t0, 2), len(human)])
        for (x, y, w, h) in human:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
        cv2.putText(frame, f"people: {len(human)}  (q: quit)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("People counter", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        n += 1

    cap.release()
    cv2.destroyAllWindows()
    f.close()
    print("保存しました:", args.out)


if __name__ == "__main__":
    main()
