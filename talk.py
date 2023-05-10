import socket
import pyaudio
import wave
import time
import os
from google.cloud import speech, speech_v1
import openai
import subprocess
import threading
from src import MicrophoneStream

# Settings for julius
JULIUS_HOST = 'localhost'
JULIUS_PORT = 10500

# Settings for pyaudio
A_SAMPLE_RATE = 16000
A_CHUNK = int(A_SAMPLE_RATE / 10)
A_FORMAT = pyaudio.paInt16
A_CHANNELS = 1 # モノラル入力
A_REC_SEC = 4 # 録音秒数
A_OUTPUT_FILE = 'tmp/saved.wav'
A_DEVICE_INDEX = 0

# create pyaudio instance
audio = pyaudio.PyAudio()

# create connection for Julius server
j_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
j_socket.connect((JULIUS_HOST, JULIUS_PORT))

current_time = 0
def measure_time_start():
    global current_time
    current_time = time.time()

def measure_time_end():
    global current_time
    print('[INFO] ' + str(time.time() - current_time) + 'sec')


messages = [
    {"role": "system", "content": "あなたは機動戦士ガンダムシリーズに登場する架空のロボット「ハロ」です。"},
    {"role": "system", "content": "制約条件もとに回答してください。"},
    {"role": "system", "content": "制約条件：回答は短い文章を2回繰り返す形で、「主語＋述語」の形で回答してください。"},
    {"role": "system", "content": "制約条件：敬語は使用しないでください。"},
    {"role": "system", "content": "制約条件：「〜です」「〜だ」「〜します」や口語は使用しないでください。"},
    {"role": "system", "content": "例えば、「今日の天気は？」と聞いたら「今日は晴れ、今日は晴れ」のような形です。"}
]
inputed = ''
try:
    while True:
        while (inputed.find('\n.') == -1):
            inputed += j_socket.recv(1024).decode()
        
        for line in inputed.split('\n'):
            if ('はろ' in line):
                g_client = speech.SpeechClient()
                g_config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=A_SAMPLE_RATE,
                    language_code="ja-JP"
                )
                g_streaming_config = speech.StreamingRecognitionConfig(
                    config=g_config,
                    single_utterance=True,
                    enable_voice_activity_events=True,
                    interim_results=True # If false, only is_final=true are returned.
                )

                print('[INFO] stream start')
                speeched_text = ''
                last_responsed_time = time.time()
                with MicrophoneStream.MicrophoneStream(A_SAMPLE_RATE, A_CHUNK) as stream:
                    audio_generator = stream.generator()
                    requests = (
                        speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator
                    )

                    responses = g_client.streaming_recognize(g_streaming_config, requests)

                    event_start = False
                    event_end = False
                    is_final = False
                    for response in responses:
                        for result in response.results:
                            event_start = True
                            if not result.is_final:
                                continue
                            speeched_text += result.alternatives[0].transcript
                            is_final = True
                        print('[INFO] you talked: ' + speeched_text)
                        if str(response.speech_event_type) == 'SpeechEventType.END_OF_SINGLE_UTTERANCE' or str(response.speech_event_type) == 'SpeechEventType.SPEECH_ACTIVITY_END':
                            event_end = True
                        if (event_start == False and event_end) or (is_final and event_end):
                            print('break')
                            break

                if(len(speeched_text.strip()) == 0):
                    print('[WARN] no speech')
                    continue

                # get open ai responce
                openai.api_key = os.getenv('OPEN_API_KEY')
                measure_time_start()
                print('[INFO] execute open ai api') 
                messages.append({ "role": "user", "content": speeched_text })
                o_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                measure_time_end()
                o_response_text = o_response.choices[0]["message"]["content"].strip()
                messages.append({ "role": "assistant", "content": o_response_text })
                print('[AI]' + o_response_text)

                # sound response text
                measure_time_start()
                o_shell = "echo '" + o_response_text + "' | " + os.getenv("OPEN_JTALK_SHELL")
                subprocess.run(o_shell, shell=True)
                measure_time_end()

        inputed = ''
except KeyboardInterrupt:
    audio.terminate()