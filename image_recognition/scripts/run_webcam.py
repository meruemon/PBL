# -*- coding: utf-8 -*-
"""
run_webcam.py ― Webカメラ映像をリアルタイム表示する最小スクリプト（.py ファイル実行の練習用）

使い方（Anaconda Prompt）:
    python scripts/run_webcam.py
'q' キーで終了．
"""
import cv2


def main():
    # 0 は内蔵カメラ．外付けカメラは 1, 2, … に変える．
    # cv2.CAP_DSHOW は Windows で起動を速くするオプション（Mac では外す）
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("カメラを開くことができません．")
        return

    print("画像幅:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("画像高さ:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("FPS:", cap.get(cv2.CAP_PROP_FPS))

    while cap.isOpened():
        ret, frame = cap.read()      # ret: 取得成功フラグ, frame: 画像
        if not ret:
            print("フレームを取得できません．終了します．")
            break
        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# このファイルを直接実行したときだけ main() を動かす（他のファイルから import されたときは動かない）
if __name__ == "__main__":
    main()
