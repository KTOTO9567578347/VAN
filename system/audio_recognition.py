print("OK")

import sounddevice as sd
print("OK")
import numpy as np
print("OK")
import librosa
print("OK")
import pickle
print("OK")
import time
print("OK")
from keras.models import load_model
print("OK_2")

model = load_model(r'./models/model_2.h5')
print("OK 3")
with open('./models/encoder_2.pkl', 'rb') as f:
    encoder = pickle.load(f)



def capture_audio(duration=2.5, sample_rate=22050):
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def noise(data):
    noise_amp = 0.035*np.random.uniform()*np.amax(data)
    data = data + noise_amp*np.random.normal(size=data.shape[0])
    return data
def stretch(data, rate=0.8):
    return librosa.effects.time_stretch(data, rate=rate)
def shift(data):
    shift_range = int(np.random.uniform(low=-5, high = 5)*1000)
    return np.roll(data, shift_range)
def pitch(data, sampling_rate = 0.8 , pitch_factor=0.7):
    return librosa.effects.pitch_shift(data, sr=sampling_rate, n_steps=pitch_factor)

def extract_features(data, sample_rate=22050):
    result = np.array([])
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    result=np.hstack((result, zcr))

    stft = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
    result = np.hstack((result, chroma_stft))

    mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mfcc))

    rms =  np.mean(librosa.feature.rms(y=data).T, axis=0)
    result = np.hstack((result, rms))

    mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mel))
    
    return result

def get_features(data, sample_rate=22050):
    res1 = extract_features(data)
    result = np.array(res1)
    
    noise_data = noise(data)
    res2 = extract_features(noise_data)
    result = np.vstack((result, res2))
    
    new_data = stretch(data)
    data_stretch_pitch = pitch(new_data, sample_rate)
    res3 = extract_features(data_stretch_pitch)
    result = np.vstack((result, res3))
    
    return result

def main():
    while True:
        audio = capture_audio(duration=2.5)
        print(np.mean(librosa.feature.rms(y=audio).T, axis=0)[0])
        if np.mean(librosa.feature.rms(y=audio).T, axis=0)[0] > 0.01:  #порог для проверки наличия звука
            features = get_features(audio)
            features = np.expand_dims(features, axis=2)
            emotion = model.predict(features)
            emotion = encoder.inverse_transform(emotion)
            print(f"Предсказанная эмоция: {emotion[0][0]}")
        else:
            print("Речь не обнаружена")
        time.sleep(1)

if __name__ == "__main__":
    main()