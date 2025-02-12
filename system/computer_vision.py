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
vid_save_path = "."

import pyaudio
import numpy as np
import time

import threading
import logging
import asyncio

class face_model:
	'''Класс модели распознавания лиц'''
	def __init__(self):
		self.model = YOLO('models/detect_face_model.pt')
	def detectMultiScale(self, frame):
		'''
		Распознать все лица на кадре frame
		args: frame - кадр cv2
		returns: list содержащий элементы вида [x координата левого нижнего угла, y координата левого нижнего угла, ширина рамки, высота рамки, ID лица]
		'''
		dat = []
		results = self.model.track(frame, verbose=False, tracker = "bytetrack.yaml", persist=True)
		
		if results[0].boxes.id != None:
			boxes = results[0].boxes.xywh.cpu()
			track_ids = results[0].boxes.id.int().cpu().tolist()

			for xywh, track_num in zip(boxes, track_ids):
				c_x, c_y, w, h = tuple(map(lambda x: int(x.item()), xywh))
				dat.append((c_x - w//2, c_y - h//2, w, h, track_num))
		return dat
	
class CV:
	'''
	Класс функций компьютерного зрения.
	'''
	def __init__(self, output_app):
		self.tracking_buffer = dict()
		self.audio_emotion_classification = '-'
		self.app = output_app
		self.resolution = 96
		self.usable_model = YOLO(r"models/classify_face.pt")
		self.rus_names = {'angry': "злость", 'fear': 'страх', 'happy': "радость", 'neutral': "спокойствие", 'sad': "грусть", 'surprise': "удивление"}
		self.face_model = face_model()
		self.vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)
		self.fourcc = cv2.VideoWriter_fourcc(*'MP42')
		self.video_write_FPS = 10.0
		self.width, self.height = 640, 480
		self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
		self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
		self.frame = None
		self.out = cv2.VideoWriter(vid_save_path + '/' + str(datetime.datetime.now())+'.avi', self.fourcc, self.video_write_FPS, (640, 480))
		self.frames_save_limit = 20
	
	def open_camera(self):
		ret, frame = self.vid.read()
		if (not ret or type(frame) == None):
			self.vid.release()
			print("NOVIDEO")
			frame = cv2.imread(r"./assets/nosignal.jpg")
		else:
			finded_faces = self.face_model.detectMultiScale(frame)
			predicted_classes = []
			table_values = []
			for (x, y, w, h, track_num) in finded_faces:
				try:
					subframe = frame[x:x+w, y:y+h]
					subframe = cv2.resize(subframe, (self.resolution, self.resolution))
					prediction = self.usable_model.predict(subframe, verbose = False)[0]
					pred_id = prediction.probs.top1
					if track_num in self.tracking_buffer.keys():
						if self.tracking_buffer[track_num].qsize() >= self.frames_save_limit:
							self.tracking_buffer[track_num].get()
						self.tracking_buffer[track_num].put(pred_id)
					else:
						self.tracking_buffer[track_num] = queue.Queue()
						self.tracking_buffer[track_num].put(pred_id)
					
					statistical_pred_id = mode(list(self.tracking_buffer[track_num].queue))

					predicted_class = self.usable_model.names[statistical_pred_id]
					cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,0),2)
					cv2.putText(frame, f"{self.rus_names[predicted_class]} {track_num}", (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0))
					predicted_classes.append(predicted_class)
					table_values.append((track_num, self.rus_names[predicted_class], '-'))
				except:
					pass

			self.app.table_data = table_values
			self.app.detected_emotion.set(str(' '.join(predicted_classes)))
		
		if (self.app.is_on_air.get()):
			self.out.write(frame)
		
		opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
		captured_image = Image.fromarray(opencv_image)
		photo_image = ImageTk.PhotoImage(image=captured_image)
		self.app.image_widget.photo_image = photo_image
		self.app.image_widget.configure(image=photo_image)
		self.app.image_widget.after(5, self.open_camera)
	
	def get_vid_save_name(self):
		return str(datetime.datetime.now()).split('.')[0].replace(' ', '_').replace(':', '_')+'.avi'

	def get_available_cameras(self) :
		devices = FilterGraph().get_input_devices()
		available_cameras = {}
		for device_index, device_name in enumerate(devices):
			available_cameras[device_index] = device_name
		return available_cameras
	
	def update_camera_list(self):
		cur_cam_list =  self.get_available_cameras()
		self.app.cameras_list_widget['value'] = [str(' '.join([str(key), cur_cam_list[key]])) for key in cur_cam_list.keys()]

	def recap_camera(self):
		global vid
		cur_cam = int(self.app.selected_camera.get().split()[0])
		print(cur_cam, " recapped")
		self.vid = cv2.VideoCapture(cur_cam, cv2.CAP_DSHOW)

	def start_record(self):
		if (self.app.is_on_air.get()):
			vid_save_name = self.get_vid_save_name()
			print("start recording of ", vid_save_name)
			self.out = cv2.VideoWriter(vid_save_name, self.fourcc, self.video_write_FPS, (640, 480))
		else:
			print("End recording...")
			self.out.release()