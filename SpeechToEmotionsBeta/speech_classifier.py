import librosa
import pyaudio
import numpy as np
import time
from keras.models import load_model
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

def extract_features(data, sample_rate):
    
    result = np.array([])
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    result=np.hstack((result, zcr)) 


    stft = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
    result = np.hstack((result, chroma_stft)) 


    mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mfcc)) 

    
    rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
    result = np.hstack((result, rms)) 


    mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mel)) 
    
    return result

pa = pyaudio.PyAudio()
model = load_model('model.keras')
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])



FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 1024

STREAM_SECONDS = 5


audio = pyaudio.PyAudio()


label_list = {'грусть': 0,
                  'злость': 0,
                  'радость': 0,
                  'спокойствие': 0,
                  'страх': 0,
                  'удивление': 0,
                  }

CHUNKS_PER_SECOND = RATE // CHUNK


def callback(in_data, frame_count, time_info, flag):
    data = np.fromstring(in_data, dtype=np.float32)
    feature = extract_features(data, RATE)
    global label_list
    X = []
    for ele in feature:
            X.append(ele)
    #print(X)
    Features = pd.DataFrame(X)
    Features = Features.transpose()
    #print(Features)
    X = Features.iloc[: ,:-1].values
    #print(X)
    #print(X.shape)
    #X = X.reshape(1, -1)  
    #X = np.expand_dims(X, axis=2)  
    #print(X)


    labels = ['грусть', 'злость', 'радость', 'спокойствие', 'страх', 'удивление']
    predictions = model.predict(Features, verbose=0)
    predicted_label = [labels[np.argmax(pred)] for pred in predictions][0]
    label_list[predicted_label] += 1
    if sum(label_list.values()) == CHUNKS_PER_SECOND:
         print(max(label_list))
         print(label_list)
         label_list = {'грусть': 0,
                  'злость': 0,
                  'радость': 0,
                  'спокойствие': 0,
                  'страх': 0,
                  'удивление': 0,
                  }
         

    return None, pyaudio.paContinue

in_stream = audio.open(format=FORMAT, 
                    channels=CHANNELS,
                    rate=RATE, 
                    input=True,
                    input_device_index=1, #< ----- Input index device
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

print("*record started")
    





in_stream.start_stream()
while in_stream.is_active():
    time.sleep(0.25)
in_stream.close()
pa.terminate()