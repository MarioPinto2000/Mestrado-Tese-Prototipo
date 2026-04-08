"""
Sistema Multimodal - Módulo de Debug e Análise de Landmarks
Função: Fornecer ferramentas para visualizar e analisar os dados dos landmarks em tempo real
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple


class HandAnalyzer:
    """
    Classe para análise e visualização detalhada dos landmarks da mão
    Útil para debugging e desenvolvimento de reconhecimento de gestos
    """
    
    # Nomes dos landmarks para visualização
    LANDMARK_NAMES = {
        0: "Pulso", 1: "Polegar-CMC", 2: "Polegar-MCP", 3: "Polegar-IP", 4: "Polegar-TIP",
        5: "Indicador-MCP", 6: "Indicador-PIP", 7: "Indicador-DIP", 8: "Indicador-TIP",
        9: "Médio-MCP", 10: "Médio-PIP", 11: "Médio-DIP", 12: "Médio-TIP",
        13: "Anelar-MCP", 14: "Anelar-PIP", 15: "Anelar-DIP", 16: "Anelar-TIP",
        17: "Mínimo-MCP", 18: "Mínimo-PIP", 19: "Mínimo-DIP", 20: "Mínimo-TIP"
    }
    
    @staticmethod
    def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calcula a distância euclidiana entre dois pontos
        
        Args:
            point1: (x, y) primeira coordenada
            point2: (x, y) segunda coordenada
            
        Returns:
            float: Distância euclidiana
        """
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    @staticmethod
    def calculate_angle(point1: Tuple[float, float], 
                       vertex: Tuple[float, float], 
                       point2: Tuple[float, float]) -> float:
        """
        Calcula o ângulo entre três pontos (em graus)
        
        Args:
            point1: Primeiro ponto
            vertex: Vértice do ângulo
            point2: Terceiro ponto
            
        Returns:
            float: Ângulo em graus (0-180)
        """
        # Vetores
        v1 = np.array([point1[0] - vertex[0], point1[1] - vertex[1]])
        v2 = np.array([point2[0] - vertex[0], point2[1] - vertex[1]])
        
        # Produto escalar e magnitudes
        dot_product = np.dot(v1, v2)
        magnitude_v1 = np.linalg.norm(v1)
        magnitude_v2 = np.linalg.norm(v2)
        
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0
        
        # Cosine do ângulo
        cos_angle = dot_product / (magnitude_v1 * magnitude_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        # Converter para graus
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    @staticmethod
    def is_finger_extended(landmarks: List, finger_tip: int, finger_pip: int) -> bool:
        """
        Verifica se um dedo está estendido comparando posições
        
        Args:
            landmarks: Lista de landmarks da mão
            finger_tip: Índice do ponto da ponta do dedo
            finger_pip: Índice do ponto anterior (PIP)
            
        Returns:
            bool: True se o dedo está estendido
        """
        return landmarks[finger_tip].y < landmarks[finger_pip].y
    
    @staticmethod
    def count_extended_fingers(landmarks: List) -> dict:
        """
        Conta quantos dedos estão estendidos
        
        Args:
            landmarks: Lista de 21 landmarks da mão
            
        Returns:
            dict: Dicionário com contagem por dedo
        """
        fingers = {
            'thumb': HandAnalyzer.is_finger_extended(landmarks, 4, 3),
            'index': HandAnalyzer.is_finger_extended(landmarks, 8, 6),
            'middle': HandAnalyzer.is_finger_extended(landmarks, 12, 10),
            'ring': HandAnalyzer.is_finger_extended(landmarks, 16, 14),
            'pinky': HandAnalyzer.is_finger_extended(landmarks, 20, 18)
        }
        
        return fingers
    
    @staticmethod
    def get_hand_orientation(landmarks: List) -> str:
        """
        Determina a orientação da mão (palma para cima, para baixo, lado)
        
        Args:
            landmarks: Lista de landmarks da mão
            
        Returns:
            str: 'up', 'down', 'left', 'right' ou 'unknown'
        """
        # Usar a profundidade (z) para determinar orientação
        palm_y = landmarks[9].y  # Médio-MCP
        pinky_y = landmarks[17].y  # Mínimo-MCP
        
        # Se o médio está acima do mínimo, palma virada para cima
        if palm_y < pinky_y:
            return "palm_up"
        else:
            return "palm_down"
    
    @staticmethod
    def draw_landmarks_with_info(image: np.ndarray, 
                                 landmarks: List,
                                 show_labels: bool = True) -> np.ndarray:
        """
        Desenha landmarks com informações adicionais
        
        Args:
            image: Frame do vídeo
            landmarks: Lista de landmarks
            show_labels: Se deve mostrar nomes dos landmarks
            
        Returns:
            np.ndarray: Imagem com informações desenhadas
        """
        h, w, _ = image.shape
        
        # Desenhar círculos para cada landmark
        for idx, landmark in enumerate(landmarks):
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            
            # Diferentes cores para diferentes dígitos
            if idx == 0:  # Pulso
                color = (255, 0, 0)  # Azul
                radius = 8
            elif 1 <= idx <= 4:  # Polegar
                color = (0, 255, 255)  # Amarelo
                radius = 6
            elif 5 <= idx <= 8:  # Indicador
                color = (0, 255, 0)  # Verde
                radius = 6
            elif 9 <= idx <= 12:  # Médio
                color = (255, 0, 255)  # Magenta
                radius = 6
            elif 13 <= idx <= 16:  # Anelar
                color = (255, 165, 0)  # Laranja
                radius = 6
            else:  # Mínimo
                color = (255, 0, 0)  # Vermelho
                radius = 6
            
            cv2.circle(image, (x, y), radius, color, -1)
            
            if show_labels and idx < len(HandAnalyzer.LANDMARK_NAMES):
                cv2.putText(image, str(idx), (x + 10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return image
    
    @staticmethod
    def print_hand_analysis(landmarks: List) -> None:
        """
        Imprime análise detalhada da mão no console
        
        Args:
            landmarks: Lista de landmarks da mão
        """
        print("\n" + "="*50)
        print("ANÁLISE DA MÃO")
        print("="*50)
        
        # Contar dedos estendidos
        extended = HandAnalyzer.count_extended_fingers(landmarks)
        extended_count = sum(extended.values())
        print(f"\nDedos Estendidos: {extended_count}/5")
        for finger, is_extended in extended.items():
            status = "✓ Estendido" if is_extended else "✗ Fechado"
            print(f"  {finger.upper()}: {status}")
        
        # Orientação da mão
        orientation = HandAnalyzer.get_hand_orientation(landmarks)
        print(f"\nOrientação: {orientation}")
        
        # Distâncias importantes
        print("\nDistâncias (normalizadas):")
        thumb_index_distance = HandAnalyzer.calculate_distance(
            (landmarks[4].x, landmarks[4].y),
            (landmarks[8].x, landmarks[8].y)
        )
        print(f"  Polegar-Indicador: {thumb_index_distance:.3f}")
        
        # Coordenadas dos pontos importantes
        print("\nCoordenadas dos Dedos (normalizadas):")
        important_points = {
            'Polegar': 4,
            'Indicador': 8,
            'Médio': 12,
            'Anelar': 16,
            'Mínimo': 20
        }
        
        for name, idx in important_points.items():
            print(f"  {name}: ({landmarks[idx].x:.3f}, {landmarks[idx].y:.3f}, {landmarks[idx].z:.3f})")
        
        print("="*50 + "\n")


def main_debug():
    """
    Função principal para modo debug com análise de landmarks
    """
    import sys
    sys.path.insert(0, '/home/claude')
    from gestures.hand_detector import HandDetector
    
    detector = HandDetector()
    analyzer = HandAnalyzer()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Erro: Não foi possível abrir a webcam")
        return
    
    print("Modo DEBUG - Análise de Landmarks")
    print("Pressione 'q' para sair, 'p' para imprimir análise")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame, (640, 480))
        frame, hands_landmarks, confidences = detector.detect_hands(frame)
        
        if hands_landmarks:
            # Desenhar com informações
            frame = analyzer.draw_landmarks_with_info(frame, hands_landmarks[0], show_labels=True)
            
            # Informações básicas
            extended = analyzer.count_extended_fingers(hands_landmarks[0])
            extended_count = sum(extended.values())
            cv2.putText(frame, f"Dedos: {extended_count}/5", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("DEBUG - Análise de Landmarks", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p') and hands_landmarks:
            analyzer.print_hand_analysis(hands_landmarks[0])
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main_debug()
