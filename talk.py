import socket
import pyaudio
import wave

# Settings for julius
JULIUS_HOST = 'localhost'
JULIUS_PORT = 10500

# Settings for pyaudio
A_CHUNK = 1024 * 4
A_FORMAT = pyaudio.paInt16
A_CHANNELS = 1 # モノラル入力
A_SAMPLE_RATE = 44100 # 44.1kHz サンプリング周波数
A_REC_SEC = 3 # 録音秒数
A_OUTPUT_FILE = 'tmp/saved.wav'
A_DEVICE_INDEX = 0

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
            print('[INFO] recording start for ' + A_REC_SEC + ' minutes')
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
	
    inputed = ''


audio.terminate()
