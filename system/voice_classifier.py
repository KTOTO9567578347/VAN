from transformers import HubertForSequenceClassification, Wav2Vec2FeatureExtractor
import torchaudio
import torch

TOKEN = "XXX"
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/hubert-large-ls960-ft", token = TOKEN)
model = HubertForSequenceClassification.from_pretrained("xbgoose/hubert-speech-emotion-recognition-russian-dusha-finetuned", token = TOKEN)
num2emotion = {0: 'neutral', 1: 'angry', 2: 'positive', 3: 'sad', 4: 'other'}

filepath = "test1.wav"

waveform, sample_rate = torchaudio.load(filepath, normalize=True)
transform = torchaudio.transforms.Resample(sample_rate, 16000)
waveform = transform(waveform)

inputs = feature_extractor(
        waveform, 
        sampling_rate=feature_extractor.sampling_rate, 
        return_tensors="pt",
        padding=True,
        max_length=16000 * 10,
        truncation=True
    )

logits = model(inputs['input_values'][0]).logits
predictions = torch.argmax(logits, dim=-1)
predicted_emotion = num2emotion[predictions.numpy()[0]]
print(predicted_emotion)