import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        self.command_mode_active = False
        self.zoom_mode_active = False
        self.last_command_time = 0
        self.cooldown = 3.0 
        
        self.index_anchor_x = None
        self.pinky_anchor_x = None
        self.swipe_threshold = 0.12 
        
        self.prev_right_hand_open = False 
        self.prev_right_hand_closed = False

    def get_cooldown_status(self):
        current_time = time.time()
        elapsed = current_time - self.last_command_time
        remaining = max(0, self.cooldown - elapsed)
        return remaining == 0, remaining

    def _can_execute(self) -> bool:
        ready, _ = self.get_cooldown_status()
        if ready:
            self.last_command_time = time.time()
            return True
        return False

    def update_state(self, labels: List[str], hands_landmarks: List[List], analyzer) -> bool:
        self.command_mode_active = False 
        self.zoom_mode_active = False
        
        for i, label in enumerate(labels):
            if label == "Left":
                fingers = analyzer.count_extended_fingers(hands_landmarks[i])
                ind, med = fingers['index'], fingers['middle']
                outros_fechados = not fingers['ring'] and not fingers['pinky']

                if ind and not med and outros_fechados:
                    self.command_mode_active = True
                elif ind and med and outros_fechados:
                    self.zoom_mode_active = True
        
        if not self.command_mode_active:
            self.index_anchor_x = None
            self.pinky_anchor_x = None
                
        return self.command_mode_active or self.zoom_mode_active

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not self.command_mode_active and not self.zoom_mode_active:
            return "Aguardando Ativador (Mao Esq.)"

        for i, label in enumerate(labels):
            if label == "Right":
                hand = hands_landmarks[i]
                fingers = analyzer.count_extended_fingers(hand)
                
                # --- NOVA LÓGICA: IGNORAR POLEGAR ---
                # causa conflitos
                dedos_principais = [fingers['index'], fingers['middle'], fingers['ring'], fingers['pinky']]
                total_sem_polegar = sum(dedos_principais)
                
                # --- MODO NAVEGAÇÃO (SLIDE) ---
                if self.command_mode_active:
                    
                    if total_sem_polegar == 1:
                        # 1. APENAS INDICADOR
                        if fingers['index']:
                            self.pinky_anchor_x = None
                            current_x = hand[8].x 
                            if self.index_anchor_x is None:
                                self.index_anchor_x = current_x
                                return "INDICADOR PRONTO"

                            displacement = current_x - self.index_anchor_x
                            if abs(displacement) > self.swipe_threshold:
                                if self._can_execute():
                                    pyautogui.press('right')
                                    self.index_anchor_x = current_x
                                    return "SWIPE: Próximo >>"
                            return "Movendo Indicador..."

                        # 2. APENAS MINDINHO
                        elif fingers['pinky']:
                            self.index_anchor_x = None
                            current_x = hand[20].x 
                            if self.pinky_anchor_x is None:
                                self.pinky_anchor_x = current_x
                                return "MINDINHO PRONTO"

                            displacement = current_x - self.pinky_anchor_x
                            if abs(displacement) > self.swipe_threshold:
                                if self._can_execute():
                                    pyautogui.press('left')
                                    self.pinky_anchor_x = current_x
                                    return "SWIPE: Anterior <<"
                            return "Movendo Mindinho..."
                    
                    self.index_anchor_x = None
                    self.pinky_anchor_x = None
                    return "Use apenas Indicador ou Mindinho"

                # --- MODO ZOOM ---
                elif self.zoom_mode_active:
                    
                    dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
                    if dist_ok < 0.10 and fingers['middle'] and fingers['pinky']:
                        if self._can_execute():
                            pyautogui.hotkey('ctrl', 'alt', '0')
                            return "RESET ZOOM"

                    
                    abertos_total = sum(fingers.values())
                    mão_aberta, mão_fechada = abertos_total >= 4, abertos_total <= 1
                    
                    if self.prev_right_hand_closed and mão_aberta:
                        if self._can_execute():
                            for _ in range(3): pyautogui.hotkey('ctrl', '+')
                            self.prev_right_hand_closed = False 
                            return "Zoom In"
                    elif self.prev_right_hand_open and mão_fechada:
                        if self._can_execute():
                            for _ in range(3): pyautogui.hotkey('ctrl', '-')
                            self.prev_right_hand_open = False 
                            return "Zoom Out"

                self.prev_right_hand_open = (sum(fingers.values()) >= 4)
                self.prev_right_hand_closed = (sum(fingers.values()) <= 1)
                return "Modo Ativo"
    
        return "Mão Direita não detectada"