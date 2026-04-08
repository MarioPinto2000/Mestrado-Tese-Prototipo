#!/usr/bin/env python3
"""
Script de Instalação - Sistema Multimodal
Verifica e instala automaticamente todas as dependências necessárias
"""

import subprocess
import sys
import os
from pathlib import Path


class Installer:
    """Classe para gerenciar instalação de dependências"""
    
    def __init__(self):
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.os_type = sys.platform
        
    def print_header(self):
        """Imprime cabeçalho"""
        print("\n" + "="*60)
        print("SISTEMA MULTIMODAL - INSTALAÇÃO")
        print("="*60)
        print(f"Python: {self.python_version}")
        print(f"Sistema Operativo: {self.os_type}")
        print("="*60 + "\n")
    
    def check_python_version(self):
        """Verifica se a versão do Python é compatível"""
        major, minor = sys.version_info.major, sys.version_info.minor
        
        if major < 3 or (major == 3 and minor < 8):
            print("❌ Erro: Python 3.8 ou superior é necessário")
            print(f"   Versão atual: {self.python_version}")
            return False
        
        print(f"✓ Python {self.python_version} compatível")
        return True
    
    def check_package(self, package_name: str, import_name: str = None) -> bool:
        """
        Verifica se um pacote está instalado
        
        Args:
            package_name: Nome do pacote (para instalar)
            import_name: Nome para importar (se diferente)
            
        Returns:
            bool: True se instalado, False caso contrário
        """
        import_name = import_name or package_name.split('==')[0]
        
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
    
    def install_requirements(self):
        """Instala as dependências do arquivo requirements.txt"""
        requirements_file = Path(__file__).parent / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ Arquivo requirements.txt não encontrado")
            return False
        
        print("📦 Instalando dependências...")
        print("-" * 60)
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file)
            ])
            print("-" * 60)
            print("✓ Dependências instaladas com sucesso\n")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}\n")
            return False
    
    def verify_installation(self):
        """Verifica se todas as dependências foram instaladas"""
        print("🔍 Verificando instalação...")
        print("-" * 60)
        
        packages = {
            'opencv-python': 'cv2',
            'mediapipe': 'mediapipe',
            'numpy': 'numpy'
        }
        
        all_installed = True
        
        for package, import_name in packages.items():
            if self.check_package(package, import_name):
                print(f"✓ {package}")
            else:
                print(f"❌ {package}")
                all_installed = False
        
        print("-" * 60 + "\n")
        
        return all_installed
    
    def create_project_structure(self):
        """Cria a estrutura de pastas do projeto"""
        print("📁 Criando estrutura do projeto...")
        
        directories = [
            "config",
            "modules",
            "tests",
            "data",
            "logs"
        ]
        
        for directory in directories:
            path = Path(__file__).parent / directory
            path.mkdir(exist_ok=True)
            print(f"  ✓ {directory}/")
        
        print()
    
    def print_next_steps(self):
        """Imprime próximos passos"""
        print("="*60)
        print("✓ INSTALAÇÃO CONCLUÍDA!")
        print("="*60)
        print("\n📝 Próximos Passos:")
        print("  1. Execute o detector de mão:")
        print("     python hand_detector.py")
        print("\n  2. Para análise detalhada de landmarks:")
        print("     python hand_analyzer.py")
        print("\n  3. Consulte README.md para mais informações")
        print("\n" + "="*60 + "\n")
    
    def run(self):
        """Executa o processo de instalação"""
        self.print_header()
        
        # 1. Verificar Python
        if not self.check_python_version():
            return False
        
        # 2. Instalar dependências
        if not self.install_requirements():
            return False
        
        # 3. Verificar instalação
        if not self.verify_installation():
            print("⚠️  Algumas dependências podem não estar corretamente instaladas")
            print("   Tente executar manualmente:")
            print("   pip install -r requirements.txt")
            return False
        
        # 4. Criar estrutura
        self.create_project_structure()
        
        # 5. Próximos passos
        self.print_next_steps()
        
        return True


def main():
    """Função principal"""
    try:
        installer = Installer()
        success = installer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação cancelada pelo utilizador")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante instalação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
