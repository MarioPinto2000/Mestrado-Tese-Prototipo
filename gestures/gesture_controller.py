import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        self.command_mode_active = False
        self.zoom_mode_active = False
        self.last_command_time = 0
        self.cooldown = 3.0 
        
        # Memória para movimento da mão direita
        self.prev_right_hand_open = False 
        self.prev_right_hand_closed = False

    def get_cooldown_status(self):
        """Retorna se está pronto e o tempo restante para o HUD do Main."""
        current_time = time.time()
        elapsed = current_time - self.last_command_time
        remaining = max(0, self.cooldown - elapsed)
        return remaining == 0, remaining

    def _can_execute(self) -> bool:
        """Verifica se pode executar e atualiza o tempo se True."""
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
                ind = fingers['index']
                med = fingers['middle']
                outros_fechados = not fingers['ring'] and not fingers['pinky']

                if ind and not med and outros_fechados:
                    self.command_mode_active = True
                elif ind and med and outros_fechados:
                    self.zoom_mode_active = True
                
        return self.command_mode_active or self.zoom_mode_active

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not self.command_mode_active and not self.zoom_mode_active:
            return "Aguardando Ativador (Mao Esq.)"

        for i, label in enumerate(labels):
            if label == "Right":
                hand = hands_landmarks[i]
                fingers = analyzer.count_extended_fingers(hand)
                abertos = sum(fingers.values())
                
                mão_aberta = abertos >= 4
                mão_fechada = abertos <= 1

                # --- MODO ZOOM ---
                if self.zoom_mode_active:
                    # GESTO OK (Reset PPT: Ctrl+Alt+0)
                    dist_ok = analyzer.calculate_distance((hand[4].x, hand[4].y), (hand[8].x, hand[8].y))
                    
                    if dist_ok < 0.10 and fingers['middle'] and fingers['pinky']:
                        if self._can_execute():
                            pyautogui.hotkey('ctrl', 'alt', '0')
                            return "GESTO: Zoom Original (PPT)"

                    # Zoom In: Fechar -> Abrir
                    if self.prev_right_hand_closed and mão_aberta:
                        if self._can_execute():
                            for _ in range(3):
                                pyautogui.hotkey('ctrl', '+')
                            self.prev_right_hand_closed = False 
                            return "GESTO: Zoom In +++"
                    
                    # Zoom Out: Abrir -> Fechar
                    elif self.prev_right_hand_open and mão_fechada:
                        if self._can_execute():
                            for _ in range(3):
                                pyautogui.hotkey('ctrl', '-')
                            self.prev_right_hand_open = False 
                            return "GESTO: Zoom Out ---"

                # --- MODO NAVEGAÇÃO (Slide) ---
                elif self.command_mode_active:
                    if fingers['index'] and abertos == 1:
                        if self._can_execute():
                            pyautogui.press('right')
                            return "SLIDE: Proximo"
                    elif fingers['thumb'] and abertos == 1:
                        if self._can_execute():
                            pyautogui.press('left')
                            return "SLIDE: Anterior"

                # Atualiza a memória de movimento
                self.prev_right_hand_open = mão_aberta
                self.prev_right_hand_closed = mão_fechada
                
                return "Modo Zoom Ativo" if self.zoom_mode_active else "Modo Slide Ativo"
    
        return "Mao Direita nao detectada"