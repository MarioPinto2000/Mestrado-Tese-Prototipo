import json
import os
import time
from pathlib import Path

class MetricsLogger:
    def __init__(self):
        self.start_time = time.time()
        
        self.feedback_dir = "feedback"
        self.local_file = os.path.join(self.feedback_dir, "historico_sessoes.json")
        self.backup_file = os.path.join(str(Path.home()), ".PowerPointGestures_metrics.json")
        
        # Métricas da Sessão Atual
        self.gesture_frames_processed = 0
        self.gesture_latencies = []
        self.gestures_executed = 0  
        
        self.voice_attempts = 0
        self.voice_latencies = []
        self.voice_success = 0

    def log_gesture_frame(self, latency_ms):
        self.gesture_frames_processed += 1
        self.gesture_latencies.append(latency_ms)

    def log_gesture_attempt(self, executed=True):
        """Soma +1 sempre que um comando de gesto correto é executado."""
        self.gestures_executed += 1

    def log_voice_attempt(self, latency_ms, success=False):
        self.voice_attempts += 1
        self.voice_latencies.append(latency_ms)
        if success:
            self.voice_success += 1

    def _load_existing_history(self):
        if os.path.exists(self.local_file):
            try:
                with open(self.local_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass 

        if os.path.exists(self.backup_file):
            try:
                with open(self.backup_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
                
        return {"total_sessoes_registadas": 0, "dados_globais_acumulados": {}, "historico": []}

    def save_report(self):
        end_time = time.time()
        duration_seconds = end_time - self.start_time

        # 1. Cálculos da sessão que acabou de correr
        avg_gesture_latency = sum(self.gesture_latencies) / len(self.gesture_latencies) if self.gesture_latencies else 0.0
        avg_voice_latency = sum(self.voice_latencies) / len(self.voice_latencies) if self.voice_latencies else 0.0
        voice_accuracy = (self.voice_success / self.voice_attempts * 100) if self.voice_attempts > 0 else 0.0

        dados_historicos = self._load_existing_history()
        proxima_sessao_id = dados_historicos.get("total_sessoes_registadas", 0) + 1

        dados_sessao_atual = {
            "sessao_id": proxima_sessao_id,
            "data_execucao": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            "informacao_geral": {
                "duracao_da_sessao_segundos": round(duration_seconds, 2),
                "total_frames_processados": self.gesture_frames_processed
            },
            "metricas_gestos": {
                "latencia_media_ms": round(avg_gesture_latency, 2),
                "total_gestos_executados": self.gestures_executed
            },
            "metricas_voz": {
                "latencia_media_reconhecimento_ms": round(avg_voice_latency, 2),
                "total_tentativas_voz": self.voice_attempts,
                "total_comandos_reconhecidos": self.voice_success,
                "taxa_precisao_voz_percentual": round(voice_accuracy, 2)
            }
        }

        todas_sessoes = dados_historicos.get("historico", []) + [dados_sessao_atual]

        total_tempo = sum(s["informacao_geral"]["duracao_da_sessao_segundos"] for s in todas_sessoes)
        total_frames = sum(s["informacao_geral"]["total_frames_processados"] for s in todas_sessoes)
        
        total_gestos_executados = sum(s["metricas_gestos"]["total_gestos_executados"] for s in todas_sessoes)
        
        media_latencia_gestos_global = (
            sum(s["metricas_gestos"]["latencia_media_ms"] * s["informacao_geral"]["total_frames_processados"] for s in todas_sessoes) / total_frames
            if total_frames > 0 else 0.0
        )

        total_tentativas_voz = sum(s["metricas_voz"]["total_tentativas_voz"] for s in todas_sessoes)
        total_comandos_reconhecidos = sum(s["metricas_voz"]["total_comandos_reconhecidos"] for s in todas_sessoes)
        precisao_voz_global = (total_comandos_reconhecidos / total_tentativas_voz * 100) if total_tentativas_voz > 0 else 0.0

        media_latencia_voz_global = (
            sum(s["metricas_voz"]["latencia_media_reconhecimento_ms"] * s["metricas_voz"]["total_tentativas_voz"] for s in todas_sessoes) / total_tentativas_voz
            if total_tentativas_voz > 0 else 0.0
        )

        dados_globais = {
            "numero_total_de_testes": proxima_sessao_id,
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

        dados_historicos["total_sessoes_registadas"] = proxima_sessao_id
        dados_historicos["dados_globais_acumulados"] = dados_globais
        dados_historicos["historico"] = todas_sessoes

        if not os.path.exists(self.feedback_dir):
            os.makedirs(self.feedback_dir)

        with open(self.local_file, "w", encoding="utf-8") as f:
            json.dump(dados_historicos, f, indent=4, ensure_ascii=False)

        try:
            with open(self.backup_file, "w", encoding="utf-8") as f:
                json.dump(dados_historicos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[MÉTRICAS] Erro no backup: {e}")
        
        print(f"\n[MÉTRICAS] Sessão #{proxima_sessao_id} concluída e adicionada aos dados globais!")