# -*- coding: utf-8 -*-
"""
yolo_detect.py ― YOLOv5 (ONNX) + OpenCV DNN による物体検出スクリプト

Webカメラ・動画ファイル・画像ファイルのどれにでも使える．検出結果をCSVに記録できる．
'q' キーで終了．

使い方（Anaconda Prompt，image_recognition フォルダで）:
    python scripts/yolo_detect.py --source 0                          # Webカメラ
    python scripts/yolo_detect.py --source data/vtest.avi --csv data/yolo.csv
    python scripts/yolo_detect.py --source data/img/img01.jpg --save out.jpg
    python scripts/yolo_detect.py --model det/best.onnx --names det/my.names --source 0   # 自作モデル

CSV の列: time（秒 or 経過秒）, frame, object, conf, x, y, w, h
"""
import argparse
import csv
import time
from pathlib import Path

import cv2
import numpy as np

INPUT_SIZE = 640
BLUE, YELLOW, BLACK = (255, 178, 50), (0, 255, 255), (0, 0, 0)


def load_model(model_path: str, names_path: str):
    net = cv2.dnn.readNet(model_path)
    classes = Path(names_path).read_text(encoding="utf-8").strip().split("\n")
    return net, classes


def detect_objects(net, classes, img, conf_th=0.45, score_th=0.5, nms_th=0.45):
    """画像(BGR) → [(クラス名, 信頼度, (x, y, w, h)), ...]"""
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (INPUT_SIZE, INPUT_SIZE), swapRB=True, crop=False)
    net.setInput(blob)
    out = net.forward(net.getUnconnectedOutLayersNames())[0][0]
    boxes, confs, ids = [], [], []
    for row in out:
        conf = float(row[4])
        if conf < conf_th:
            continue
        scores = row[5:]
        cid = int(np.argmax(scores))
        if scores[cid] < score_th:
            continue
        cx, cy, bw, bh = row[:4]
        boxes.append([int((cx - bw / 2) * w / INPUT_SIZE), int((cy - bh / 2) * h / INPUT_SIZE),
                      int(bw * w / INPUT_SIZE), int(bh * h / INPUT_SIZE)])
        confs.append(conf)
        ids.append(cid)
    keep = cv2.dnn.NMSBoxes(boxes, confs, conf_th, nms_th)
    keep = [int(i) for i in np.array(keep).ravel()] if len(keep) else []
    return [(classes[ids[i]], confs[i], tuple(boxes[i])) for i in keep]


def draw(img, detections):
    for name, conf, (x, y, w, h) in detections:
        cv2.rectangle(img, (x, y), (x + w, y + h), BLUE, 2)
        label = f"{name}: {conf:.2f}"
        (tw, th), base = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(img, (x, y), (x + tw, y + th + base), BLACK, cv2.FILLED)
        cv2.putText(img, label, (x, y + th), cv2.FONT_HERSHEY_SIMPLEX, 0.6, YELLOW, 1, cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser(description="YOLOv5 ONNX detection with OpenCV")
    ap.add_argument("--source", default="0", help="0 (Webカメラ) / 動画ファイル / 画像ファイル")
    ap.add_argument("--model", default="det/yolov5s.onnx")
    ap.add_argument("--names", default="det/coco.names")
    ap.add_argument("--csv", default=None, help="検出結果を書き出すCSVファイル")
    ap.add_argument("--save", default=None, help="画像入力のとき，結果画像の保存先")
    ap.add_argument("--every", type=int, default=1, help="Nフレームごとに検出（動画を軽くする）")
    ap.add_argument("--conf", type=float, default=0.45)
    args = ap.parse_args()

    net, classes = load_model(args.model, args.names)
    writer = None
    if args.csv:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        f = open(args.csv, "w", newline="", encoding="utf-8-sig")
        writer = csv.writer(f)
        writer.writerow(["time", "frame", "object", "conf", "x", "y", "w", "h"])

    src = args.source
    is_image = Path(src).suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    if is_image:
        img = cv2.imread(src)
        dets = detect_objects(net, classes, img, conf_th=args.conf)
        for name, conf, (x, y, w, h) in dets:
            print(f"{name:12s} {conf:.2f}  ({x}, {y}, {w}, {h})")
            if writer:
                writer.writerow([0, 0, name, round(conf, 3), x, y, w, h])
        out = draw(img, dets)
        if args.save:
            cv2.imwrite(args.save, out)
            print("saved:", args.save)
        cv2.imshow("YOLOv5", out)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    cap = cv2.VideoCapture(int(src), cv2.CAP_DSHOW) if src.isdigit() else cv2.VideoCapture(src)
    if not cap.isOpened():
        raise SystemExit(f"入力を開けません: {src}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    is_camera = src.isdigit()
    t0 = time.time()
    frame_no = 0
    dets = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_no % args.every == 0:
            dets = detect_objects(net, classes, frame, conf_th=args.conf)
            t = round(time.time() - t0, 2) if is_camera else round(frame_no / fps, 2)
            if writer:
                for name, conf, (x, y, w, h) in dets:
                    writer.writerow([t, frame_no, name, round(conf, 3), x, y, w, h])
        frame = draw(frame, dets)
        cv2.putText(frame, f"objects: {len(dets)}  (q: quit)", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("YOLOv5 Object Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        frame_no += 1
    cap.release()
    cv2.destroyAllWindows()
    if writer:
        f.close()
        print("CSV saved:", args.csv)


if __name__ == "__main__":
    main()
