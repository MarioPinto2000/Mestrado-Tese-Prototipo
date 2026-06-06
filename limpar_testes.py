import os
import json
import shutil
from pathlib import Path

local_file = os.path.join("feedback", "historico_sessoes.json")
backup_file = os.path.join(str(Path.home()), ".PowerPointGestures_metrics.json")

def recalcular_e_atualizar_json(caminho_ficheiro, id_para_remover):
    if not os.path.exists(caminho_ficheiro):
        return False

    try:
        with open(caminho_ficheiro, "r", encoding="utf-8") as f:
            dados = json.load(f)

        historico_original = dados.get("historico", [])
        # Filtra e remove a sessão pretendida
        historico_filtrado = [s for s in historico_original if s.get("sessao_id") != id_para_remover]

        # Se o tamanho for igual, significa que este ID não existia no ficheiro
        if len(historico_original) == len(historico_filtrado):
            return False

        # --- RECONSTRUÇÃO COMPATÍVEL COM O METRICS_LOGGER ---
        if not historico_filtrado:
            # Se não sobrarem sessões, faz reset completo à estrutura
            dados["total_sessoes_registadas"] = 0
            dados["dados_globais_acumulados"] = {
                "numero_total_de_testes": 0,
                "tempo_acumulado_testes_segundos": 0.0,
                "total_frames_analisados": 0,
                "gestos_global": {
                    "latencia_media_geral_ms": 0.0,
                    "total_comandos_executados": 0
                },
                "voz_global": {
                    "latencia_media_geral_ms": 0.0,
                    "total_tentativas_audio": 0,
                    "total_comandos_reconhecidos": 0,
                    "taxa_precisao_geral_percentual": 0.0
                }
            }
            dados["historico"] = []
        else:
            # Recalcula os totais baseando-se estritamente na matemática do teu MetricsLogger
            total_tempo = sum(s["informacao_geral"]["duracao_da_sessao_segundos"] for s in historico_filtrado)
            total_frames = sum(s["informacao_geral"]["total_frames_processados"] for s in historico_filtrado)
            
            # Métricas de Gesto
            total_gestos_executados = sum(s["metricas_gestos"]["total_gestos_executados"] for s in historico_filtrado)
            sessoes_com_latencia_gesto = [s for s in historico_filtrado if s["metricas_gestos"]["latencia_media_ms"] > 0]
            media_latencia_gestos_global = (
                sum(s["metricas_gestos"]["latencia_media_ms"] for s in sessoes_com_latencia_gesto) / len(sessoes_com_latencia_gesto)
                if sessoes_com_latencia_gesto else 0.0
            )

            # Métricas de Voz
            total_tentativas_voz = sum(s["metricas_voz"]["total_tentativas_voz"] for s in historico_filtrado)
            total_comandos_reconhecidos = sum(s["metricas_voz"]["total_comandos_reconhecidos"] for s in historico_filtrado)
            sessoes_com_latencia_voz = [s for s in historico_filtrado if s["metricas_voz"]["latencia_media_reconhecimento_ms"] > 0]
            media_latencia_voz_global = (
                sum(s["metricas_voz"]["latencia_media_reconhecimento_ms"] for s in sessoes_com_latencia_voz) / len(sessoes_com_latencia_voz)
                if sessoes_com_latencia_voz else 0.0
            )
            precisao_voz_global = (total_comandos_reconhecidos / total_tentativas_voz * 100) if total_tentativas_voz > 0 else 0.0

            # Atualiza os dados mantendo o ID máximo atual como o total de registos
            dados["total_sessoes_registadas"] = max(s["sessao_id"] for s in historico_filtrado)
            dados["dados_globais_acumulados"] = {
                "numero_total_de_testes": len(historico_filtrado),
                "tempo_acumulado_testes_segundos": round(total_tempo, 2),
                "total_frames_analisados": total_frames,
                "gestos_global": {
                    "latencia_media_geral_ms": round(media_latencia_gestos_global, 2),
                    "total_comandos_executados": total_gestos_executados
                },
                "voz_global": {
                    "latencia_media_geral_ms": round(media_latencia_voz_global, 2),
                    "total_tentativas_audio": total_tentativas_voz,
                    "total_comandos_reconhecidos": total_comandos_reconhecidos,
                    "taxa_precisao_geral_percentual": round(precisao_voz_global, 2)
                }
            }
            dados["historico"] = historico_filtrado

        # Grava de volta as alterações mantendo a codificação utf-8 e indentação original
        with open(caminho_ficheiro, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao processar o ficheiro {caminho_ficheiro}: {e}")
        return False


# --- INTERFACE DE EXECUÇÃO VIA TERMINAL ---
print("--- REMOVER SESSÃO ESPECÍFICA DO HISTÓRICO ---")
try:
    id_alvo = int(input("Introduza o ID da sessão que pretende eliminar (ex: 9): "))
    
    atualizou_local = recalcular_e_atualizar_json(local_file, id_alvo)
    atualizou_backup = recalcular_e_atualizar_json(backup_file, id_alvo)

    if atualizou_local or atualizou_backup:
        print(f"\n[SUCESSO] A sessão ID {id_alvo} foi removida!")
        if atualizou_local: print(f"[OK] Ficheiro atualizado: {local_file}")
        if atualizou_backup: print(f"[OK] Cópia oculta de segurança atualizada.")
    else:
        print(f"\n[AVISO] O ID {id_alvo} não foi encontrado em nenhum dos ficheiros de métricas.")

except ValueError:
    print("\n[ERRO] Entrada inválida. Por favor, digite um número inteiro correspondente ao 'sessao_id'.")