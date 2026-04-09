import pyautogui
import time
from typing import List, Dict

class GestureController:
    def __init__(self):
        self.command_mode_active = False
        self.last_command_time = 0
        self.cooldown = 3.0  

    def update_state(self, labels: List[str], hands_landmarks: List[List], analyzer) -> bool:
        self.command_mode_active = False 
        
        for i, label in enumerate(labels):
            if label == "Left":
                fingers = analyzer.count_extended_fingers(hands_landmarks[i])
                abertos = sum(fingers.values())
                
                # Punho fechado (0 ou 1 dedo aberto)
                if abertos <= 1:
                    self.command_mode_active = True
                
        return self.command_mode_active

    def get_right_hand_command(self, labels: List[str], hands_landmarks: List[List], analyzer) -> str:
        if not self.command_mode_active:
            return "Aguardando Ativador (Mao Esq. Fechada)"

        current_time = time.time()

        for i, label in enumerate(labels):
            if label == "Right":
                hand = hands_landmarks[i]
                fingers = analyzer.count_extended_fingers(hand)
                
                # Assinatura de dedos: (Polegar, Indicador, Médio, Anelar, Mínimo)
                gesto_atual = (
                    fingers['thumb'],
                    fingers['index'],
                    fingers['middle'],
                    fingers['ring'],
                    fingers['pinky']
                )

                # --- GESTO 1: PRÓXIMO SLIDE (Só Indicador) ---
                if gesto_atual == (False, True, False, False, False):
                    dist_indicador = analyzer.calculate_distance(
                        (hand[8].x, hand[8].y), (hand[5].x, hand[5].y)
                    )
                    
                    if dist_indicador > 0.12: 
                        if (current_time - self.last_command_time) > self.cooldown:
                            pyautogui.press('right')
                            self.last_command_time = current_time
                            return "EXECUTADO: Proximo Slide"
                        else:
                            return "Aguarde o Cooldown..."
                    else:
                        return "Estique mais o indicador"

                # --- GESTO 2: SLIDE ANTERIOR (Só Polegar) ---
                elif gesto_atual == (True, False, False, False, False):
                    dist_polegar = analyzer.calculate_distance(
                        (hand[4].x, hand[4].y), (hand[5].x, hand[5].y)
                    )
                    
                    if dist_polegar > 0.10:
                        if (current_time - self.last_command_time) > self.cooldown:
                            pyautogui.press('left')
                            self.last_command_time = current_time
                            return "EXECUTADO: Slide Anterior"
                        else:
                            return "Aguarde o Cooldown..."
                    else:
                        return "Estique mais o polegar"

                return "Modo Ativo: Faca um gesto claro"
    
        return "Modo Ativo: Mao Direita nao detectada"