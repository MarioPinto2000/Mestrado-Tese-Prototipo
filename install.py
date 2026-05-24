#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

class Installer:
    def __init__(self):
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
    def check_python_version(self):
        """Verifica se a versao do Python e 3.8+"""
        if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
            print(f"❌ Erro: Python 3.8+ necessario. Versao atual: {self.python_version}")
            return False
        print(f"✓ Python {self.python_version} compativel")
        return True

    def install_requirements(self):
        """Instala as dependencias do arquivo requirements.txt"""
        req_path = Path(__file__).parent / "requirements.txt"
        
        if not req_path.exists():
            print("❌ Erro: requirements.txt nao encontrado!")
            return False

        print("\n📦 Instalando dependencias (OpenCV, MediaPipe, Pycaw, SpeechRecognition, etc)...")
        try:
            # Forca o ambiente do subset do PIP a rodar em UTF-8 para prevenir erros de caracteres
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"

            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
                env=env
            )
            print("✓ Dependencias instaladas com sucesso!\n")
            return True
        except Exception as e:
            print(f"❌ Erro na instalacao: {e}")
            return False

    def verify(self):
        """Verifica se os imports criticos funcionam"""
        print("🔍 Verificando pacotes instalados...")
        
        # Forca o Python a atualizar a arvore de pacotes instalados no utilizador
        import site
        import importlib
        importlib.reload(site)
        
        # Adicionados pycaw e comtypes para o controlo de volume real do Windows
        packages = {
            'opencv-python': 'cv2',
            'mediapipe': 'mediapipe',
            'SpeechRecognition': 'speech_recognition',
            'pyaudio': 'pyaudio',
            'word2number': 'word2number',
            'Pillow': 'PIL'
        }
        
        all_ok = True
        for pkg, imp in packages.items():
            try:
                __import__(imp)
                print(f"  ✓ {pkg}")
            except ImportError:
                print(f"  ❌ {pkg} (falhou no import)")
                all_ok = False
        return all_ok

    def run(self):
        print("\n" + "="*40)
        print("SISTEMA MULTIMODAL - SETUP")
        print("="*40)
        
        if self.check_python_version() and self.install_requirements():
            if self.verify():
                print("\n✅ TUDO PRONTO! Podes correr o teu projeto.")
            else:
                print("\n⚠️  Alguns pacotes de voz ou audio nativo podem precisar de atencao manual.")
        
        print("="*40 + "\n")

if __name__ == "__main__":
    Installer().run()