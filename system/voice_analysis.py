import queue
from PIL import Image, ImageTk 
import datetime
import tkinter as tk
from statistics import mode
from tkinter import ttk
import cv2
from pygrabber.dshow_graph import FilterGraph
from sys import exit
from voice_classifier import VoiceClassifier
from computer_vision import CV
import numpy as np

vid_save_path = "."

import pyaudio
import librosa
import pickle
import time
import torch
import torch.nn as nn


import threading
import logging
import asyncio



class audio_processor:
	def __init__(self, output_app):
		self.classifier = VoiceClassifier()
		self.app = output_app
		self.is_on_air_now = False
		self.FORMAT = pyaudio.paFloat32
		self.CHANNELS = 1
		self.RATE = 22050
		self.CHUNK = 1024
		self.duration = 2.5
		self.audio_frames_buffer = np.array([], dtype=np.float32)
		self.required_samples = int(self.RATE * self.duration)
		self.is_recording_now = False
		self.pa = pyaudio.PyAudio()

		self.in_stream = self.pa.open(format=pyaudio.paFloat32,
			start=False,
	        channels=1,
	        rate=self.RATE,
	        output=False,
	        input=True,
	        stream_callback=self.callback,
			input_device_index = 1)
	
		self.out_stream = self.pa.open(format=self.FORMAT, 
					start=False,
		            channels=self.CHANNELS,
		            rate=self.RATE, 
		            output=True,
		            input_device_index=2,
		            frames_per_buffer=self.CHUNK)
		
	def callback(self, in_data, frame_count, time_info, flag):
		new_data = np.frombuffer(in_data, dtype=np.float32)
			
		self.audio_frames_buffer = np.append(self.audio_frames_buffer, new_data)
			
		if len(self.audio_frames_buffer) >= self.required_samples:
			process_data = self.audio_frames_buffer
			#self.play_sound()   
			self.clear_buffer()
			self.process_audio(process_data)
        
		return None, pyaudio.paContinue

	def process_audio(self, audio_data):
		try:
			rms = np.mean(librosa.feature.rms(y=audio_data))
			if rms < 0.003:
				voice_class = "тишина"
				spectrogram_image = None
			else:
				voice_class = self.classifier.process_audio_frames(audio_data)
				spectrogram_image = self.app.spectrogram_generator.get_spectogram_image(audio_data, self.RATE)
			
			self.app.logged_voice_emotion.set(voice_class)
			self.app.refresh_voice_class(voice_class)
			
			if spectrogram_image:
				self.app.spectrogram_label.imgtk = spectrogram_image
				self.app.spectrogram_label.configure(image=spectrogram_image)
				
		except Exception as e:
			print(f"Ошибка обработки аудио: {str(e)}")
		###
	def start_recording(self):
		print("*recording")
		self.in_stream.start_stream()
	
	def stop_recording(self):
		print("*stop record")
		self.in_stream.stop_stream()
	
	def play_sound(self):
		sound_to_play = self.audio_frames_buffer.copy()
		self.clear_buffer()
		self.out_stream.start_stream()
		print("playing sound")
		for data in sound_to_play:
			self.out_stream.write(data.tobytes())
		print("stop playing sound")
		self.out_stream.stop_stream()
	
	def clear_buffer(self):
		self.audio_frames_buffer = np.array([], dtype=np.float32)
	
	def audio_relay(self):
		print("RELAY ACTIVE")
		if (self.app.is_audio_on_air.get()):
			self.start_recording()
		else:
			self.stop_recording()

	def get_microphones(self):
		p = pyaudio.PyAudio()
		microphones = []
		for i in range(p.get_device_count()):
			try:
				device_info = p.get_device_info_by_index(i)
				if device_info.get('maxInputChannels') > 0:
					microphones.append(device_info.get('name'))
			except OSError as e:
				print(f"Error accessing device {i}: {e}")
		self.app.audio_list_widget['value'] = microphones    
	def on_microphone_select(self):
		selected_mic = int(self.app.selected_audio.get().split()[0])        
		print(f"Выбран микрофон: {selected_mic}")
		self.aud = selected_mic