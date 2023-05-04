import socket
import pyaudio
import wave
import time
import os
from google.cloud import speech

# Settings for julius
JULIUS_HOST = 'localhost'
JULIUS_PORT = 10500

# Settings for pyaudio
A_CHUNK = 1024 * 4
A_FORMAT = pyaudio.paInt16
A_CHANNELS = 1 # モノラル入力
A_SAMPLE_RATE = 44100 # 44.1kHz サンプリング周波数
A_REC_SEC = 5 # 録音秒数
A_OUTPUT_FILE = 'tmp/saved.wav'
A_DEVICE_INDEX = 0


print(os.getenv('COMMAND_JULIUS_MODULE'))


# create pyaudio instance
audio = pyaudio.PyAudio()

# create connection for Julius server
j_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
j_socket.connect((JULIUS_HOST, JULIUS_PORT))

inputed = ''
while True:
    while (inputed.find('\n.') == -1):
        inputed += j_socket.recv(1024).decode()
    
    for line in inputed.split('\n'):
        if ('はろ' in line):
            # open audio stream
            print('[INFO] detect talk to me')
            stream = audio.open(format=A_FORMAT,rate=A_SAMPLE_RATE,channels=A_CHANNELS,input=True, frames_per_buffer=A_CHUNK)
            print('[INFO] recording start for ' + str(A_REC_SEC) + ' minutes')
            frames = []
            for i in range(0,int((A_SAMPLE_RATE/A_CHUNK)*A_REC_SEC)):
                data = stream.read(A_CHUNK)
                frames.append(data)
            print('[INFO] recording finish')
            stream.stop_stream()
            stream.close()

            # save to .wav
            wavefile = wave.open(A_OUTPUT_FILE, 'wb')
            wavefile.setnchannels(A_CHANNELS)
            wavefile.setsampwidth(audio.get_sample_size(A_FORMAT))
            wavefile.setframerate(A_SAMPLE_RATE)
            wavefile.writeframes(b''.join(frames))
            wavefile.close()
            print('[INFO] saved .wav file')

            # create speech to text settings
            g_client = speech.SpeechClient()
           
            with open(A_OUTPUT_FILE, "rb") as speech_file:
                g_content = speech_file.read()

            g_audio = speech.RecognitionAudio(content=g_content)
            g_config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,sample_rate_hertz=A_SAMPLE_RATE,language_code="ja-JP")
            g_operation = g_client.long_running_recognize(config=g_config, audio=g_audio)
           
            # execute speech to text api
            print('[INFO] execute GCP speech to text API...')
            g_response = g_operation.result(timeout=90)
            
            speeched_text = ''
            for result in g_response.results:
                speeched_text += u"{ }".format(result.alternatives[0].transcript)
            print(speeched_text)

    inputed = ''


audio.terminate()
