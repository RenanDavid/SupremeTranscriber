import pyaudio
import vosk
import pyperclip
import subprocess
import json
import time
import os

class TranscriberController:
    def __init__(self, model_path, pause_threshold=10.0, mic_index=None):
        """
        :param model_path: Caminho absoluto para a pasta do modelo Vosk (PT-BR ou outro).
        :param pause_threshold: Tempo (segundos) de pausa para considerar 'novo tópico'.
        :param mic_index: Índice do dispositivo de áudio (microfone). Se None, usa default.
        """
        self.model_path = model_path
        self.pause_threshold = pause_threshold
        self.mic_index = mic_index

        # Carrega o modelo do Vosk
        self.model = vosk.Model(self.model_path)
        self.is_running = False

        # Texto acumulado no bloco atual
        self.segment_text = ""
        # Timestamp do último áudio recebido (partial ou final)
        self.last_audio_time = time.time()
        # Flag para indicar se estamos "no meio" de um segmento
        self.segment_active = False

    def start_transcription(self):
        self.is_running = True

        p = pyaudio.PyAudio()
        
        # Se não foi escolhido microfone específico, usa o device padrão (None)
        device_index = None
        if self.mic_index is not None:
            device_index = self.mic_index
        
        print(f"[DEBUG] Abrindo stream com device_index={device_index}")

        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096,
            input_device_index=device_index
        )

        recognizer = vosk.KaldiRecognizer(self.model, 16000)

        print(f"[DEBUG] Iniciando transcrição com pause_threshold={self.pause_threshold}s")
        print("[DEBUG] Use CTRL+C para encerrar manualmente.\n")

        try:
            while self.is_running:
                data = stream.read(4096, exception_on_overflow=False)
                current_time = time.time()

                # Verifica se a diferença de tempo ultrapassa o threshold (pausa longa)
                if (current_time - self.last_audio_time) > self.pause_threshold:
                    print("[DEBUG] Detected long pause. Reiniciando bloco/segmento.")
                    # Zera o texto do segmento
                    self.segment_text = ""
                    self.segment_active = False

                    # Resetar o clipboard (string vazia)
                    self.update_clipboard("")

                # Atualiza a marca de tempo da última atividade de áudio
                self.last_audio_time = current_time

                # Processamento do chunk de áudio
                if recognizer.AcceptWaveform(data):
                    # Temos um resultado final
                    result_json = recognizer.Result()  # {"text": "..."}
                    parsed = json.loads(result_json)
                    texto_final = parsed.get("text", "")

                    if texto_final:
                        # Marca que estamos num segmento ativo, caso não estivéssemos
                        if not self.segment_active:
                            self.segment_active = True
                            self.segment_text = ""

                        # Concatena este final ao texto do segmento
                        if self.segment_text:
                            self.segment_text += " "
                        self.segment_text += texto_final

                        # Aqui chamamos a função de tratamento do texto
                        texto_com_pontuacao = format_text_for_punctuation(self.segment_text)

                        # Copiamos para o clipboard a versão formatada
                        self.update_clipboard(texto_com_pontuacao)

                        print(f"[DEBUG - FINAL] {texto_final}")
                        print(f"[DEBUG - SEGMENTO ATUAL SEM FORMATAÇÃO] {self.segment_text}")
                        print(f"[DEBUG - SEGMENTO ATUAL FORMATADO]      {texto_com_pontuacao}\n")

                else:
                    # partial
                    partial_json = recognizer.PartialResult()
                    partial_parsed = json.loads(partial_json)
                    texto_parcial = partial_parsed.get("partial", "")
                    if texto_parcial:
                        print(f"[DEBUG - PARCIAL] {texto_parcial}")

        except KeyboardInterrupt:
            print("[DEBUG] CTRL+C detectado, saindo.")
        except Exception as e:
            print("[ERRO] Exceção na transcrição:", e)
        finally:
            print("[DEBUG] Encerrando stream de áudio...")
            stream.stop_stream()
            stream.close()
            p.terminate()

    def stop_transcription(self):
        print("[DEBUG] stop_transcription() chamado, encerrando a captura.")
        self.is_running = False

    def update_clipboard(self, text):
        """
        Copia o 'text' para o clipboard.
        Se pyperclip falhar, tenta fallback no Windows (clip) ou Linux (xclip).
        """
        try:
            pyperclip.copy(text)
        except Exception as e:
            print("[DEBUG] Falha ao usar pyperclip, tentando fallback:", e)
            if os.name == 'nt':
                # Windows
                subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
            else:
                # Linux
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)


def format_text_for_punctuation(texto):
    """
    Função simples (e ingênua) para adicionar vírgulas em certas conjunções
    e melhorar um pouco a pontuação.
    
    - Adiciona vírgula antes de algumas conjunções (e, mas, então, porém).
    - Coloca maiúscula no início da string.
    - Exemplos:
        "ola e como voce esta mas tudo bem entao vamos" -> "Ola, e como voce esta, mas tudo bem, entao vamos"
    """
    # Converte tudo para minúsculo antes, se quiser padronizar:
    # (ou pode manter a forma que o Vosk trouxe)
    lower_text = texto.strip().lower()

    # Vamos inserir vírgulas antes de algumas conjunções
    # Observação: é algo bem rudimentar, pois pode inserir vírgulas demais
    conjuncoes = [" e ", " mas ", " porém ", " entao ", " então "]

    for conj in conjuncoes:
        # Substitui " conj" por ", conj"
        # Exemplo: " e " -> ", e "
        lower_text = lower_text.replace(conj, f",{conj.strip()} ")

    # Coloca letra maiúscula no começo do texto
    if len(lower_text) > 1:
        lower_text = lower_text[0].upper() + lower_text[1:]

    return lower_text.strip()
