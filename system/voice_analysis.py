import queue
from PIL import Image, ImageTk 
import datetime
from ultralytics import YOLO
import tkinter as tk
from statistics import mode
from tkinter import ttk
import cv2
from pygrabber.dshow_graph import FilterGraph
from sys import exit
#from voice_classifier import VoiceClassifier
vid_save_path = "."

import pyaudio
import numpy as np
import time

import threading
import logging
import asyncio

class audio_processor:
	def __init__(self, output_app):
		#параметры захвата звука. 
		self.audio_play_thread = threading.Thread(target = self.play_sound)
		self.app = output_app
		self.is_on_air_now = False
		self.FORMAT = pyaudio.paFloat32
		self.CHANNELS = 1
		self.RATE = 16000
		self.CHUNK = 1024
		self.audio_frames_buffer = []
		self.is_recording_now = False
		self.pa = pyaudio.PyAudio()
		#self.classifier = VoiceClassifier()

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
		audio_data = np.fromstring(in_data, dtype=np.float32)
		self.audio_frames_buffer.append(audio_data)
		#######
		# -- обработка звука
		#######
		
		voice_class = 1 #self.classifier.process_audio_frames(self.audio_frames_buffer, self.RATE)
		self.app.refresh_voice_class(voice_class)
		return None, pyaudio.paContinue

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
		self.audio_frames_buffer.clear()
	
	def audio_relay(self):
		print("RELAY ACTIVE")
		if (self.app.is_audio_on_air.get()):
			self.start_recording()
		else:
			self.stop_recording()