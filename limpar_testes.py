import os
import shutil
from pathlib import Path

# Caminhos dos ficheiros
local_file = os.path.join("feedback", "historico_sessoes.json")
backup_file = os.path.join(str(Path.home()), ".PowerPointGestures_metrics.json")

print("--- A LIMPAR HISTÓRICO DE TESTES ---")

# 1. Elimina o ficheiro local (ou a pasta feedback)
if os.path.exists(local_file):
    os.remove(local_file)
    print("[OK] Ficheiro local em 'feedback/' removido.")
elif os.path.exists("feedback"):
    shutil.rmtree("feedback")
    print("[OK] Pasta 'feedback/' removida.")

# 2. Elimina a cópia de segurança oculta do sistema
if os.path.exists(backup_file):
    os.remove(backup_file)
    print("[OK] Cópia de segurança oculta do sistema removida.")

print("\n[SUCESSO] O histórico foi resetado. Pronto para o próximo utilizador!")