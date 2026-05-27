import speech_recognition as sr
import pyautogui
from word2number import w2n

class VoiceController:
    # Modificado para aceitar o índice do microfone selecionado na interface
    def __init__(self, mic_index=None):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(device_index=mic_index)
        self.is_listening = False 

    def listen_for_slide(self):
        self.is_listening = True
        text = ""
        comando_confirmado = ""
        with self.mic as source:
            print("A ouvir...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio, language='en-US').lower()
                print(f"🗣️ Voz detectada: {text}")

                if "slide" in text or "go to" in text:
                    target_number = None
                    words = text.split()
                    
                    for word in words:
                        if word.isdigit():
                            target_number = word
                            break

                    if not target_number:
                        try:
                            num_val = w2n.word_to_num(text)
                            target_number = str(num_val)
                        except ValueError:
                            pass

                    if target_number:
                        print(f"Comando executado: Slide {target_number}")
                        pyautogui.write(target_number)
                        pyautogui.press('enter')
                            
            except Exception as e:
                print(f"Erro na voz: {e}")
        
        self.is_listening = False
        return text, comando_confirmado