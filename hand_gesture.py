import cv2
import mediapipe as mp
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from collections import deque
import threading
import queue

class HandWorldCoordinateDetector:
    def __init__(self, 
                 static_image_mode=False,
                 max_num_hands=2,
                 model_complexity=1,
                 min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        """
        MediaPipe Handsの初期化
        
        Parameters:
        -----------
        static_image_mode : bool
            静止画モード（動画の場合はFalse）
        max_num_hands : int
            検出する手の最大数
        model_complexity : int
            モデルの複雑度（0または1）
        min_detection_confidence : float
            検出の信頼度閾値
        min_tracking_confidence : float
            トラッキングの信頼度閾値
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # 手の接続情報（骨格構造）
        self.hand_connections = self.mp_hands.HAND_CONNECTIONS
    
    def process_frame(self, frame):
        """
        フレームから手のランドマークを検出し、ワールド座標を取得
        
        Parameters:
        -----------
        frame : numpy.ndarray
            入力画像（BGR形式）
        
        Returns:
        --------
        results : mediapipe results object
            検出結果
        """
        # BGRからRGBに変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # MediaPipeで処理
        results = self.hands.process(rgb_frame)
        
        return results
    
    def get_world_landmarks(self, results):
        """
        検出結果からワールド座標を取得
        
        Parameters:
        -----------
        results : mediapipe results object
            検出結果
        
        Returns:
        --------
        world_landmarks_list : list
            各手のワールド座標リスト（メートル単位）
        """
        world_landmarks_list = []
        
        if results.multi_hand_world_landmarks:
            for hand_world_landmarks in results.multi_hand_world_landmarks:
                landmarks = []
                for landmark in hand_world_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,  # メートル単位のX座標
                        'y': landmark.y,  # メートル単位のY座標
                        'z': landmark.z   # メートル単位のZ座標（手首を原点とする）
                    })
                world_landmarks_list.append(landmarks)
        
        return world_landmarks_list
    
    def get_normalized_landmarks(self, results):
        """
        検出結果から正規化座標を取得
        
        Parameters:
        -----------
        results : mediapipe results object
            検出結果
        
        Returns:
        --------
        normalized_landmarks_list : list
            各手の正規化座標リスト（0-1の範囲）
        """
        normalized_landmarks_list = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,  # 正規化X座標（0-1）
                        'y': landmark.y,  # 正規化Y座標（0-1）
                        'z': landmark.z   # 正規化Z座標（相対深度）
                    })
                normalized_landmarks_list.append(landmarks)
        
        return normalized_landmarks_list
    
    def draw_landmarks(self, frame, results):
        """
        フレーム上にランドマークを描画
        
        Parameters:
        -----------
        frame : numpy.ndarray
            描画対象の画像
        results : mediapipe results object
            検出結果
        
        Returns:
        --------
        frame : numpy.ndarray
            ランドマークが描画された画像
        """
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        return frame
    
    def display_world_coordinates(self, frame, world_landmarks_list):
        """
        ワールド座標をフレーム上に表示
        
        Parameters:
        -----------
        frame : numpy.ndarray
            表示対象の画像
        world_landmarks_list : list
            ワールド座標のリスト
        
        Returns:
        --------
        frame : numpy.ndarray
            座標情報が表示された画像
        """
        y_offset = 30
        
        for hand_idx, landmarks in enumerate(world_landmarks_list):
            cv2.putText(frame, f"Hand {hand_idx + 1} World Coordinates (meters):", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 25
            
            # 主要なランドマークのワールド座標を表示
            key_landmarks = {
                0: "Wrist",
                4: "Thumb tip",
                8: "Index tip",
                12: "Middle tip",
                16: "Ring tip",
                20: "Pinky tip"
            }
            
            for idx, name in key_landmarks.items():
                if idx < len(landmarks):
                    landmark = landmarks[idx]
                    text = f"{name}: X={landmark['x']:.3f}, Y={landmark['y']:.3f}, Z={landmark['z']:.3f}"
                    cv2.putText(frame, text, (20, y_offset), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    y_offset += 20
            
            y_offset += 10
        
        return frame
    
    def __del__(self):
        """デストラクタ"""
        self.hands.close()


class Hand3DVisualizer:
    def __init__(self, max_hands=2):
        """
        3D手骨格ビジュアライザーの初期化
        
        Parameters:
        -----------
        max_hands : int
            表示する手の最大数
        """
        self.max_hands = max_hands
        self.fig = None
        self.ax = None
        self.lines = []
        self.points = []
        self.data_queue = queue.Queue()
        self.is_running = False
        
        # MediaPipeの手の接続情報
        self.connections = list(mp.solutions.hands.HAND_CONNECTIONS)
        
        # 各指の色設定
        self.finger_colors = {
            'thumb': 'red',      # 親指
            'index': 'orange',   # 人差し指
            'middle': 'yellow',  # 中指
            'ring': 'green',     # 薬指
            'pinky': 'blue'      # 小指
        }
        
    def setup_plot(self):
        """3Dプロットの初期設定"""
        plt.ion()  # インタラクティブモード
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # グラフの設定
        self.ax.set_xlabel('X (m)', fontsize=12)
        self.ax.set_ylabel('Y (m)', fontsize=12)
        self.ax.set_zlabel('Z (m)', fontsize=12)
        self.ax.set_title('Hand Skeleton 3D Visualization', fontsize=14, fontweight='bold')
        
        # 軸の範囲設定（メートル単位）
        self.ax.set_xlim([-0.15, 0.15])
        self.ax.set_ylim([-0.15, 0.15])
        self.ax.set_zlim([-0.15, 0.15])
        
        # グリッド表示
        self.ax.grid(True, alpha=0.3)
        
        # 背景色
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        # 視点角度の設定
        self.ax.view_init(elev=20, azim=45)
        
    def get_connection_color(self, connection):
        """接続線の色を取得"""
        start_idx, end_idx = connection
        
        # 親指 (1-4)
        if start_idx in range(0, 5) or end_idx in range(0, 5):
            return self.finger_colors['thumb']
        # 人差し指 (5-8)
        elif start_idx in range(5, 9) or end_idx in range(5, 9):
            return self.finger_colors['index']
        # 中指 (9-12)
        elif start_idx in range(9, 13) or end_idx in range(9, 13):
            return self.finger_colors['middle']
        # 薬指 (13-16)
        elif start_idx in range(13, 17) or end_idx in range(13, 17):
            return self.finger_colors['ring']
        # 小指 (17-20)
        elif start_idx in range(17, 21) or end_idx in range(17, 21):
            return self.finger_colors['pinky']
        else:
            return 'gray'
    
    def update_plot(self, world_landmarks_list):
        """3Dプロットを更新"""
        if not self.is_running:
            return
            
        # 既存の描画をクリア
        self.ax.clear()
        
        # グラフの再設定
        self.ax.set_xlabel('X (m)', fontsize=12)
        self.ax.set_ylabel('Y (m)', fontsize=12)
        self.ax.set_zlabel('Z (m)', fontsize=12)
        self.ax.set_title('Hand Skeleton 3D Visualization', fontsize=14, fontweight='bold')
        
        # 軸の範囲設定
        self.ax.set_xlim([-0.15, 0.15])
        self.ax.set_ylim([-0.15, 0.15])
        self.ax.set_zlim([-0.15, 0.15])
        
        # グリッド表示
        self.ax.grid(True, alpha=0.3)
        
        # 各手について処理
        for hand_idx, landmarks in enumerate(world_landmarks_list):
            if hand_idx >= self.max_hands:
                break
            
            # ランドマークを配列に変換
            points = np.array([[lm['x'], lm['y'], lm['z']] for lm in landmarks])
            
            # 点をプロット
            self.ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
                          c='red', s=50, alpha=0.8, marker='o')
            
            # 接続線を描画
            for connection in self.connections:
                start_idx, end_idx = connection
                if start_idx < len(points) and end_idx < len(points):
                    # 接続線の座標
                    x = [points[start_idx, 0], points[end_idx, 0]]
                    y = [points[start_idx, 1], points[end_idx, 1]]
                    z = [points[start_idx, 2], points[end_idx, 2]]
                    
                    # 色を取得
                    color = self.get_connection_color(connection)
                    
                    # 線を描画
                    self.ax.plot(x, y, z, color=color, linewidth=3, alpha=0.7)
            
            # 手のインデックスを表示
            if len(points) > 0:
                self.ax.text(points[0, 0], points[0, 1], points[0, 2] + 0.02, 
                           f'Hand {hand_idx + 1}', fontsize=10, color='black')
        
        # 原点を表示
        self.ax.scatter([0], [0], [0], c='black', s=100, marker='x', alpha=0.5)
        
        # プロットを更新
        plt.draw()
        plt.pause(0.001)
    
    def start(self):
        """ビジュアライザーを開始"""
        self.is_running = True
        self.setup_plot()
    
    def stop(self):
        """ビジュアライザーを停止"""
        self.is_running = False
        if self.fig:
            plt.close(self.fig)
    
    def update_data(self, world_landmarks_list):
        """データを更新"""
        if self.is_running:
            self.update_plot(world_landmarks_list)


def main():
    """メイン関数"""
    # HandWorldCoordinateDetectorのインスタンスを作成
    detector = HandWorldCoordinateDetector(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    # 3Dビジュアライザーのインスタンスを作成
    visualizer = Hand3DVisualizer(max_hands=2)
    visualizer.start()
    
    # デフォルトカメラ（0）を使用して映像を取得
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # カメラの解像度を設定（オプション）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("Press 'q' to quit")
    print("Press 's' to save current world coordinates to file")
    print("Press 'r' to reset 3D view angle")
    
    frame_count = 0
    
    while True:
        # カメラからフレームをキャプチャ
        ret, frame = cap.read()
        if not ret:
            print("カメラからフレームを取得できませんでした。")
            break
        
        # フレームを水平反転（鏡像表示）
        frame = cv2.flip(frame, 1)
        
        # MediaPipeで手を検出
        results = detector.process_frame(frame)
        
        # ワールド座標を取得
        world_landmarks = detector.get_world_landmarks(results)
        
        # 正規化座標も取得（参考用）
        normalized_landmarks = detector.get_normalized_landmarks(results)
        
        # ランドマークを描画
        frame = detector.draw_landmarks(frame, results)
        
        # ワールド座標を表示
        frame = detector.display_world_coordinates(frame, world_landmarks)
        
        # FPS表示（オプション）
        fps = cap.get(cv2.CAP_PROP_FPS)
        cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 検出結果を表示
        cv2.imshow('Hand World Coordinates Detection', frame)
        
        # 3Dビジュアライザーを更新（フレームを間引いて負荷軽減）
        frame_count += 1
        if frame_count % 2 == 0:  # 2フレームごとに更新
            visualizer.update_data(world_landmarks)
        
        # キー入力処理
        key = cv2.waitKey(1) & 0xFF
        
        # 'q'キーで終了
        if key == ord('q'):
            break
        
        # 'r'キーで3Dビューをリセット
        elif key == ord('r'):
            if visualizer.ax:
                visualizer.ax.view_init(elev=20, azim=45)
        
        # 's'キーでワールド座標を保存
        elif key == ord('s'):
            if world_landmarks:
                # NumPy配列に変換して保存
                for hand_idx, landmarks in enumerate(world_landmarks):
                    coords = np.array([[lm['x'], lm['y'], lm['z']] for lm in landmarks])
                    filename = f'hand_{hand_idx}_world_coordinates.npy'
                    np.save(filename, coords)
                    print(f"Saved world coordinates to {filename}")
                    
                    # テキストファイルにも保存
                    txt_filename = f'hand_{hand_idx}_world_coordinates.txt'
                    with open(txt_filename, 'w') as f:
                        f.write("Landmark,X(m),Y(m),Z(m)\n")
                        for i, lm in enumerate(landmarks):
                            f.write(f"{i},{lm['x']:.6f},{lm['y']:.6f},{lm['z']:.6f}\n")
                    print(f"Saved world coordinates to {txt_filename}")
            else:
                print("No hands detected to save coordinates")
    
    # 終了時にビジュアライザーを停止
    visualizer.stop()
    
    # 終了時にカメラを解放し、ウィンドウを閉じる
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()