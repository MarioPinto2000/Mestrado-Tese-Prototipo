"""
    Este módulo implementa a detecção de mão em tempo real usando MediaPipe e OpenCV.
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class HandLandmark:
    """Estrutura para armazenar informações de um ponto de referência da mão"""
    x: float
    y: float
    z: float
    index: int

class HandDetector:
    def __init__(self, 
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.5,
                 max_num_hands=2):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
    
    def detect_hands(self, image: np.ndarray) -> Tuple[np.ndarray, List[List[HandLandmark]], List[float], List[str]]:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.hands.process(image_rgb)
        image_rgb.flags.writeable = True
    
        hands_landmarks = []
        confidences = []
        labels = []  # Nova lista para guardar "Left" ou "Right"
    
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                landmarks = []
                for idx, landmark in enumerate(hand_landmarks.landmark):
                    landmarks.append(HandLandmark(
                        x=landmark.x, y=landmark.y, z=landmark.z, index=idx
                    ))
            
                hands_landmarks.append(landmarks)
                confidences.append(handedness.classification[0].score)
                # Extrair o label ("Left" ou "Right")
                labels.append(handedness.classification[0].label)
    
        return image, hands_landmarks, confidences, labels # Agora retorna 4 valores

    def draw_hand_landmarks(self, image: np.ndarray, hand_landmarks_list: List[List[HandLandmark]]) -> np.ndarray:
        h, w, _ = image.shape
        for landmarks in hand_landmarks_list:
            for landmark in landmarks:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
                (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15), 
                (15, 16), (0, 17), (17, 18), (18, 19), (19, 20)
            ]
            for start, end in connections:
                if start < len(landmarks) and end < len(landmarks):
                    start_point = (int(landmarks[start].x * w), int(landmarks[start].y * h))
                    end_point = (int(landmarks[end].x * w), int(landmarks[end].y * h))
                    cv2.line(image, start_point, end_point, (255, 0, 0), 2)
        return image

def main():
    """Função principal interna para teste direto do módulo"""
    detector = HandDetector(min_detection_confidence=0.7, max_num_hands=2)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam")
        return
    
    print("Iniciando modo de teste do HandDetector...")
    print("Pressione 'q' para sair")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.resize(frame, (640, 480))
        
        # Processamento
        # O detect_hands já retorna o frame, os landmarks e as confianças
        _, hands_landmarks, confidences = detector.detect_hands(frame)
        
        # Desenho
        frame = detector.draw_hand_landmarks(frame, hands_landmarks)
        
        # Info na tela
        if hands_landmarks:
            for i, conf in enumerate(confidences):
                cv2.putText(frame, f"Mão {i+1}: {conf:.2f}", (10, 30 + (i*30)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Nenhuma mão detectada", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Teste Direto - Hand Detector", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()