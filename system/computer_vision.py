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
#from pyzbar import pyzbar
from time import gmtime, strftime

from datetime import datetime as dt

from warnings import filterwarnings
filterwarnings("ignore")

import pyaudio
import numpy as np
import time

import threading
import logging
import asyncio

from ultralytics import YOLO
from joblib import load
import sklearn
import numpy as np
import pandas as pd

class pass_data:
    def __init__(self, output_app):
        self.data = pd.DataFrame()
        self.app = output_app.app
    # Функция для сканирования штрих-кодов
    def scan_barcodes(self, frame):
        # Преобразуем изображение в оттенки серого для улучшения распознавания
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Ищем штрих-коды на изображении
        barcodes = pyzbar.decode(gray)
        
        # Обрабатываем найденные штрих-коды
        for barcode in barcodes:
            # Получаем данные и тип штрих-кода
            barcode_data = barcode.data.decode("utf-8")
            if 'РЖД' in barcode_data:
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                r, ind, fio, birthday = barcode_data.split(',')
                time = strftime("%Y-%m-%d %H:%M:%S", gmtime())[:-3]
                one_code = pd.DataFrame({"Дата и время": [time], "id": [ind], "ФИО": [fio], "Дата рождения": [birthday]})
                self.data = pd.concat([self.data,one_code], ignore_index=True)
                self.data = self.data.drop_duplicates()
                self.app.logged_date = birthday
                self.app.logged_name = fio
        return frame

class pose_model_y:
	def __init__(self, model_name):
		self.model = YOLO(model_name)
		
	def detection(self, frame):
		dat = []
		results = self.model.track(frame, verbose=False, tracker = "bytetrack.yaml", persist=True)
		if results[0].boxes.id != None:
			clas = results[0].boxes.cls.cpu().tolist()
			boxes = results[0].boxes.xywh.cpu()
			keypoints = results[0].keypoints.xy.cpu().tolist()
			track_ids = results[0].boxes.id.int().cpu().tolist()
            
			for cl, xywh, kp, track_num in zip(clas, boxes, keypoints, track_ids):
				c_x, c_y, w, h = tuple(map(lambda x: int(x.item()), xywh))
				dat.append((cl, c_x - w//2, c_y - h//2, w, h, kp, track_num))
		return dat
	
	def detection_draw(self, frame):
		results = self.model.track(frame, verbose=False, tracker = "bytetrack.yaml", persist=True)
		annotated_frame = results[0].plot(labels=True)
		return annotated_frame
	
class pose_model_sk:
	def __init__(self, pose_model_name, class_model_name):
		self.pose_model = YOLO(pose_model_name)
		self.class_model = load(class_model_name)
		
	def detection(self, frame):
		dat = []
		results = self.pose_model.track(frame, verbose=False, tracker = "bytetrack.yaml", persist=True)
		if results[0].boxes.id != None:
			boxes = results[0].boxes.xywh.cpu()
			keypoints = results[0].keypoints.xy.cpu().numpy()
			track_ids = results[0].boxes.id.int().cpu().tolist()
            
			for xywh, kp, track_num in zip(boxes, keypoints, track_ids):
				c_x, c_y, w, h = tuple(map(lambda x: int(x.item()), xywh))
				dat.append((c_x - w//2, c_y - h//2, w, h, kp, track_num))
		return dat
	
	def only_class(self, frame):
		detect = self.detection(frame)
		dat = []
		if detect != None:
			for x, y, w, h, kp, track_num in detect:
				clas = self.class_model.predict(kp.T.reshape(1,-1)).item()
				dat.append((clas, track_num))
		return dat
	
	def class_detect(self, frame):
		detect = self.detection(frame)
		dat = []
		if detect != None:
			for x, y, w, h, kp, track_num in detect:
				kp1=kp.T.copy()
				kp1[0]=kp1[0]/640
				kp1[1]=kp1[1]/480
				clas = self.class_model.predict(kp1.reshape(1,-1)).item()
				dat.append((x, y, w, h, clas, kp, track_num))
		return dat
	
	def class_posedraw(self, frame):
		results = self.pose_model.track(frame, verbose=False, tracker = "bytetrack.yaml", persist=True)
		annotated_frame = results[0].plot(labels=False)
		dat = []
		if results[0].boxes.id != None:
			keypoints = results[0].keypoints.xy.cpu().numpy()
			track_ids = results[0].boxes.id.int().cpu().tolist()
			
			for kp, track_num in zip(keypoints, track_ids):
				clas = self.class_model.predict(kp.T.reshape(1,-1)).item()
				dat.append((clas, track_num))
		return (annotated_frame, dat)

class face_detect_model:
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

class face_classify_model:
	def __init__(self):
		self.face_classifier = YOLO(r"models/classify_face.pt")
		self.resolution = 96
	def predict(self, frame):
		frame = cv2.resize(frame, (self.resolution, self.resolution))
		prediction = self.face_classifier.predict(frame, verbose = False)[0]
		pred_id = prediction.probs.top1
		return pred_id

class Statistic_Buffer:
	def __init__(self):
		self.tracking_buffer = dict()
		self.frames_save_limit = 20
	
	def add_one_predict(self, track_num, pred_id):
		if track_num in self.tracking_buffer.keys():
			if self.tracking_buffer[track_num].qsize() >= self.frames_save_limit:
				self.tracking_buffer[track_num].get()
			self.tracking_buffer[track_num].put(pred_id)
		else:
			self.tracking_buffer[track_num] = queue.Queue()
			self.tracking_buffer[track_num].put(pred_id)
	def queue(self, track_num):
		return mode(list(self.tracking_buffer[track_num].queue))

class CV:
	'''
	Класс функций компьютерного зрения.
	'''
	def __init__(self, output_app):
		self.pose_model = pose_model_sk("./models/yolo11n-pose.pt", "./models/pose_classifier_sklearn.joblib")
		self.face_detect_model = face_detect_model()
		self.face_classify_model = face_classify_model()

		self.audio_emotion_classification = '-'
		self.app = output_app
		self.pass_scan = pass_data(self)
		
		self.face_classnames = {0: 'ярость', 1: 'страх', 2: 'радость', 3: 'спокоен', 4: 'грусть', 5: 'удивлен', '-': '-'}
		self.pose_classnames =  {0: 'спокоен', 1: 'ярость', 2: 'радость', 3: 'усталость', 4: 'удивление', 5: 'грусть', 6: 'страх', '-':'-'}

		self.face_stat_buffer = Statistic_Buffer()
		self.pose_stat_buffer = Statistic_Buffer()
		self.is_video_on_air = True
		self.vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)
		self.fourcc = cv2.VideoWriter_fourcc(*'MP42')
		self.video_write_FPS = 10.0
		self.width, self.height = 640, 480
		self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
		self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
		self.frame = None

		print("save path: " + "../output_videos/" + str(datetime.datetime.now())+'.avi')
		self.out = cv2.VideoWriter("../output_videos/" + str(datetime.datetime.now())+'.avi', self.fourcc, self.video_write_FPS, (640, 480))
	
	def open_camera(self):
		if self.is_video_on_air:
			processing_start_time = dt.now()
			ret, frame = self.vid.read()
			if (not ret or type(frame) == None):
				return
			
			output_frame = frame.copy()
			#output_frame = self.pass_scan.scan_barcodes(output_frame)
			if (not ret or type(frame) == None):
				self.vid.release()
				print("NOVIDEO")
				frame = cv2.imread(r"./assets/nosignal.jpg")
			else:
				table_values = []

				people_faces = self.face_detect_model.detectMultiScale(frame)
				
				for (x, y, w, h, cls_pose, kp, track_num) in self.pose_model.class_detect(frame):
					cls_face = '-'
					nose_point = kp[0]
					for face in people_faces:
						x_f, y_f, w_f, h_f, _ = face
						
						if x_f <= nose_point[0] <= x_f + w_f and y_f <= nose_point[1] <= y_f + h_f and (0 not in list(frame[x_f : x_f + w_f, y_f : y_f + h_f].shape)):
							cls_face = self.face_classify_model.predict(frame[x_f : x_f + w_f, y_f : y_f + h_f])
							cv2.rectangle(output_frame, (x_f, y_f), (x_f + w_f, y_f + h_f), (255, 255, 255), 1)
							break
					
					cv2.rectangle(output_frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
					for point in kp:
						cv2.circle(output_frame, (int(point[0]), int(point[1])), 3, (255, 167, 0))


					self.face_stat_buffer.add_one_predict(track_num, cls_face)
					self.pose_stat_buffer.add_one_predict(track_num, cls_pose)

					face_predicted = self.face_classnames[self.face_stat_buffer.queue(track_num)]
					pose_predicted = self.pose_classnames[self.pose_stat_buffer.queue(track_num)]

					cv2.putText(output_frame, f"Номер:{track_num} Лицо:{face_predicted} Тело:{pose_predicted}", (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (167, 255), 1)

					table_values.append((track_num, face_predicted, pose_predicted))
				
				processing_end_time = dt.now()

				cv2.putText(output_frame, f"FPS: {int(1.5 /(processing_end_time - processing_start_time).total_seconds())}", (3, 15), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 0), 2)

				self.app.table_data = table_values

				logger_data_pose = dict()
				logger_data_face = dict()
				for track_num, face_predicted, pose_predicted in table_values:
					logger_data_face[track_num] = face_predicted
					logger_data_pose[track_num] = pose_predicted

				self.app.logged_pose_emotion.set(str(logger_data_pose))
				self.app.logged_face_emotion.set(str(logger_data_face))
			
			if (self.app.is_on_air.get()):
				self.out.write(output_frame)
			
			opencv_image = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGBA)
			captured_image = Image.fromarray(opencv_image)
			photo_image = ImageTk.PhotoImage(image=captured_image)
			self.app.image_widget.photo_image = photo_image
			self.app.image_widget.configure(image=photo_image)
			self.app.image_widget.after(5, self.open_camera)

	
	def get_vid_save_name(self):
		return "../output_videos/" + str(datetime.datetime.now()).split('.')[0].replace(' ', '_').replace(':', '_')+'.avi'

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