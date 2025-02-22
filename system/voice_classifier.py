import torch
import numpy as np
import librosa
import pickle
from torch import nn

class audio_model(nn.Module):
    def __init__(self, input_features=1, num_classes=7):
        super(audio_model, self).__init__()
        
        self.conv_layers = nn.Sequential(
            nn.Conv1d(input_features, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64), nn.ReLU(), nn.MaxPool1d(2), nn.Dropout(0.2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1), nn.BatchNorm1d(128), nn.ReLU(),
            nn.MaxPool1d(2), nn.Dropout(0.2),
            nn.Conv1d(128, 256, kernel_size=3, padding=1), nn.BatchNorm1d(256), nn.ReLU(),
            nn.MaxPool1d(2), nn.Dropout(0.2)
        )
        self.lstm1 = nn.LSTM(
            input_size=256, hidden_size=128, batch_first=True, num_layers=1
        )
        self.dropout = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(
            input_size=128, hidden_size=64, batch_first=True, num_layers=1
        )
        self.fc = nn.Sequential(
            nn.Linear(64, 64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = self.conv_layers(x)
        x = x.permute(0, 2, 1) 
        x, (hn, cn) = self.lstm1(x)
        x = self.dropout(x)
        x, (hn, cn) = self.lstm2(x)
        x = x[:, -1, :]  
        x = self.fc(x)
        return x

class VoiceClassifier:
    def __init__(self):
        self.model = audio_model(input_features=1, num_classes=7)
        self.model.load_state_dict(
            torch.load("./models//audiomodel_only_weights.pt", map_location='cpu'))
        self.model.eval()
        
        with open('./models//encoder.pkl', 'rb') as f:
            self.encoder = pickle.load(f)
    
    def extract_features(self, data, sample_rate=22050):
        result = []
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
        result.extend(zcr)

        stft = np.abs(librosa.stft(data))
        chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
        result.extend(chroma_stft)

        mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sample_rate).T, axis=0)
        result.extend(mfcc)

        rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
        result.extend(rms)

        mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sample_rate).T, axis=0)
        result.extend(mel)
        #print(len(result))
        return np.array(result)
    
    
    def indices_to_onehot(self, indices, num_classes):
        onehot = np.zeros((len(indices), num_classes))
        onehot[np.arange(len(indices)), indices] = 1
        return onehot

    def process_audio_frames(self, audio_data):
        try:        
            # Извлечение признаков
            features = self.extract_features(audio_data)
            #return len(features)
            
            # Преобразование в тензор
            input_tensor = torch.FloatTensor(features).unsqueeze(0).unsqueeze(2)
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)  # Преобразуем в вероятности
                predictions = torch.argmax(probabilities, dim=1)
            #return outputs

            predicted_indices = predictions.numpy()
            onehot_predictions = self.indices_to_onehot(predicted_indices, num_classes=7)
            predictions = self.encoder.inverse_transform(onehot_predictions)

            return predictions[0][0]

        except Exception as e:
            return f"Ошибка в модели: {str(e)}"