from flask import Flask, render_template, request, jsonify
import threading

from transcriber.capture import TranscriberController

app = Flask(__name__)

# Ajuste caminho do modelo e parâmetros
MODEL_PATH = r"D:\SupremeTranscriber\models\vosk-model-small-pt-0.3"
PAUSE_THRESHOLD = 10.0  # agora são 10 segundos

# Variável global para o controlador
transcriber_controller = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listar_microfones', methods=['GET'])
def listar_microfones():
    import pyaudio
    p = pyaudio.PyAudio()
    info = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        # listar apenas dispositivos de entrada
        if device_info.get('maxInputChannels', 0) > 0:
            info.append({
                'index': i,
                'name': device_info.get('name', '')
            })
    p.terminate()
    return jsonify(info)

@app.route('/iniciar_transcricao', methods=['POST'])
def iniciar_transcricao():
    global transcriber_controller

    # Para qualquer transcrição anterior
    if transcriber_controller and transcriber_controller.is_running:
        transcriber_controller.stop_transcription()

    data = request.json or {}
    mic_index = data.get('mic_index', None)

    # Converte mic_index para int
    if mic_index not in [None, ""]:
        mic_index = int(mic_index)
    else:
        mic_index = None

    transcriber_controller = TranscriberController(
        model_path=MODEL_PATH,
        pause_threshold=PAUSE_THRESHOLD,
        mic_index=mic_index
    )

    t = threading.Thread(target=transcriber_controller.start_transcription, daemon=True)
    t.start()

    return jsonify({'status': 'transcricao_iniciada'})

@app.route('/parar_transcricao', methods=['POST'])
def parar_transcricao():
    global transcriber_controller
    if transcriber_controller and transcriber_controller.is_running:
        transcriber_controller.stop_transcription()
        return jsonify({'status': 'transcricao_parada'})
    return jsonify({'status': 'nenhuma_transcricao_em_andamento'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
