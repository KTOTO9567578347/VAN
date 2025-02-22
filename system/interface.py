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

from voice_analysis import audio_processor
from computer_vision import CV

class main_win:
	def __init__(self):
		self.cv = CV(self)
		self.app = tk.Tk()
		self.audio_processor = audio_processor(output_app=self)
		#self.app.iconbitmap(default='assets/favicon.ico')
		self.detected_emotion = tk.StringVar()
		self.app.bind('<Escape>', lambda e: self.app.quit()) 
		self.image_widget = tk.Label(self.app) 
		self.image_widget.pack() 

		self.table_columns = ('ID', 'face_emotion', 'pose_emotion')
		self.table = ttk.Treeview(self.app, columns= self.table_columns, show = 'headings')
		self.table.heading('ID', text = 'ID человека')
		self.table.heading('face_emotion', text = 'Эмоция лица')
		self.table.heading('pose_emotion', text = 'Эмоция позы')
		self.table_data = []
		self.table.pack()

		self.selected_camera = tk.StringVar()
		self.cameras_list_widget = ttk.Combobox(self.app, width = 27, textvariable = self.selected_camera)
		self.cameras_list_widget.pack()

		self.cam_recap_but_widget = ttk.Button(text = 'захват видео выбранной камеры', command= self.cv.recap_camera)
		self.cam_recap_but_widget.pack()

		self.cam_list_update_but_widget = ttk.Button(text = 'обновить список камер', command= self.cv.update_camera_list)
		self.cam_list_update_but_widget.pack()

		self.return_but = ttk.Button(text = 'Вернуться к стартовому окну', command=self.go_to_start)
		self.return_but.pack()

		self.is_on_air = tk.BooleanVar()
		self.is_on_air_widget_checkbox = tk.Checkbutton(self.app, text = 'записывать?', variable= self.is_on_air, onvalue=1, offvalue=0, command = self.cv.start_record)
		self.is_on_air_widget_checkbox.pack()

		self.is_audio_on_air = tk.BooleanVar()
		self.is_audio_on_air_widget_checkbox = tk.Checkbutton(self.app, text = 'использовать микрофон для анализа?', variable= self.is_audio_on_air, onvalue=1, offvalue=0, command = self.audio_processor.audio_relay)
		self.is_audio_on_air_widget_checkbox.pack()

		self.voice_class_text = tk.Label(self.app, text='-')
		self.voice_class_text.pack()
		self.refresh_voice_class("-")

		#self.play_sound_button_widget = ttk.Button(text = "Проиграть звук", command= self.audio_processor.play_sound)
		#self.play_sound_button_widget.pack()

		self.logging_thread_function()
		self.cv.open_camera()
		self.app.after(500, self.update_table)
		self.app.mainloop()

	def refresh_voice_class(self, class_voice):
		self.voice_class_text.config(text=f"Текущее настроение голоса: {class_voice}")
	
	def logging_thread_function(self):
		logging.info(self.detected_emotion.get())
		self.app.after(30, self.logging_thread_function)
	
	def go_to_start(self):
		self.app.destroy()
		self.cv.vid.release()
		start_win()

	def update_table(self):
		self.table.delete(*self.table.get_children())
		for item in self.table_data:
			self.table.insert('', 'end', values=item)
		self.app.after(500, self.update_table)

class start_win:
	def __init__(self):
		self.start_window = tk.Tk()
		self.start_window.title("VAN (Video Analytic Network)")
		print("OK STARTING")

		self.start_window.geometry("400x300")

		logo_img = Image.open('./assets/data_kvantum_logo.png')
		logo_img = logo_img.resize((100, 100))
		photo_image = ImageTk.PhotoImage(logo_img)
		self.logo_widget = tk.Label(self.start_window, image=photo_image)
		self.logo_widget.pack()

		self.authors = tk.Label(self.start_window, text="Система распознавания эмоций VAN \n Разработано Дата Квантумом Кванториума СВДЖД \n Авторы: \n Казаков Вячеслав \n Поморцев Дмитрий \n Иванов Кирилл \n Холодов Иван \n Наставник: Матанцев Анатолий Александрович")
		self.authors.pack()

		start_but = ttk.Button(text = 'ЗАПУСК', master= self.start_window, command= lambda: self.start_main())
		start_but.pack()
		self.start_window.mainloop()
	def start_main(self):
			self.start_window.destroy()
			main_win()