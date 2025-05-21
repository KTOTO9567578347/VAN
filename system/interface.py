import queue
from PIL import Image, ImageTk 
import datetime
from ultralytics import YOLO
import tkinter as tk
from statistics import mode
from tkinter import ttk
import cv2
from datetime import datetime as dt
from pygrabber.dshow_graph import FilterGraph
from sys import exit
from playsound import playsound
vid_save_path = "."

import pyaudio
import numpy as np
import time

import threading
import logging
import asyncio

from csv_logger import CSVInfoLogger
from voice_analysis import audio_processor
from voice_classifier import getSpectogram
from computer_vision import CV

class main_win:
	def get_log_name(self):
		return "log_" + str(dt.now()).replace(' ', '_').replace(':', '-').replace('.', "_")

	def __init__(self):
		self.cv = CV(self)
		self.app = tk.Tk()
		self.audio_processor = audio_processor(output_app=self.app)
		#self.app.iconbitmap(default='assets/favicon.ico')
		self.spectrogram_generator = getSpectogram()
		self.csv_logger = CSVInfoLogger("../output_logs/" + self.get_log_name() + ".csv")

		self.logged_face_emotion = tk.StringVar()
		self.logged_pose_emotion = tk.StringVar()
		self.logged_voice_emotion = tk.StringVar()
		self.desicion = tk.StringVar()
		self.logged_name = None
		self.logged_date = None

		self.app.bind('<Escape>', lambda e: self.app.quit())
		self.image_widget = tk.Label(self.app, bg="#CDCDCD")
		self.image_widget.pack()

		self.MainCanvas = tk.Canvas(master=self.app, height=400, width=1920, bg="#CDCDCD", border=0)
		self.MainCanvas.pack(anchor=tk.CENTER, expand=True)

		self.table_columns = ('ID', 'face_emotion', 'pose_emotion', 'status')
		self.table = ttk.Treeview(self.app, columns=self.table_columns, show='headings')
		self.table.heading('ID', text='ID человека')
		self.table.heading('face_emotion', text='Эмоция лица')
		self.table.heading('pose_emotion', text='Эмоция позы')
		self.table.heading('status', text='Статус')
		self.table_data = []
		self.people_logs = {}
		self.dangerous_people_logs = set()
		self.positive_emotions = {'радость', 'спокойствие', 'удивление', "усталость"}
		self.negative_emotions = {'злость', 'страх', 'грусть', 'отвращение'}

		self.style = ttk.Style()
		self.style.theme_use('clam')

		self.bg_color = "#CDCDCD"
		self.accent_color = "#E21A1A"
		self.text_color = "#FFFFFF"
		self.alt_text_color = "#000000"

		self.style.configure('TButton',
							foreground=self.text_color,
							background=self.accent_color,
							bordercolor=self.accent_color,
							font=('Helvetica', 15, 'bold'),
							padding=6)
		self.style.map('TButton',
					background=[('active', self.accent_color), ('disabled', self.bg_color)],
					foreground=[('active', self.text_color), ('disabled', self.text_color)])

		self.style.configure('TCombobox',
							fieldbackground=self.text_color,
							background=self.text_color,
							bordercolor=self.accent_color,
							arrowcolor=self.accent_color)

		self.style.configure('Treeview.Heading',
							background=self.accent_color,
							foreground=self.text_color,
							font=('Helvetica', 15, 'bold'))
		self.style.configure('Treeview',
							background=self.text_color,
							fieldbackground=self.text_color,
							rowheight=25)
		self.style.map('Treeview',
					background=[('selected', self.accent_color)])

		self.style.configure('Danger.Treeview', background=self.accent_color)
		self.table.tag_configure('danger', background=self.accent_color)

		self.spectrogram_label = tk.Label(self.app, bg="#CDCDCD", width=300, height=150)


		self.selected_camera = tk.StringVar()
		self.cameras_list_widget = ttk.Combobox(self.app, width=27, textvariable = self.selected_camera)

		
		self.selected_audio = tk.StringVar()        
		self.audio_list_widget = ttk.Combobox(self.app, width = 50, textvariable = self.selected_audio)

		self.spectrogram_label = tk.Label(self.app, bg="#CDCDCD")
		self.MainCanvas.create_window((1200, 40), window=self.spectrogram_label, anchor=tk.NW)

		self.cam_recap_but_widget = ttk.Button(text='Захват видео',
										 style='TButton',
										 command= self.cv.recap_camera
										 )
		self.cam_list_update_but_widget = ttk.Button(text='Обновить камеры',
											command= self.cv.update_camera_list
											)
		self.return_but = ttk.Button(text='Вернуться',
							   command=self.go_to_start
							   )

		self.is_on_air = tk.BooleanVar()
		self.is_on_air_widget_checkbox = tk.Checkbutton(
			self.app,
			text='Активировать запись видео',
			bg=self.bg_color,
			selectcolor=self.bg_color,
			activebackground=self.accent_color,
			disabledforeground=self.accent_color,
			fg=self.alt_text_color,
			activeforeground='white',
			font=('Helvetica', 15),
			variable=self.is_on_air,
			onvalue=1,
			offvalue=0,
			command=self.cv.start_record
		)

		self.is_on_air.trace_add('write', lambda *_, cb=self.is_on_air_widget_checkbox, var=self.is_on_air:
								cb.config(fg=self.accent_color if var.get() else self.alt_text_color)
								)
		self.is_on_air.trace_add('write', lambda *_, cb=self.is_on_air_widget_checkbox, var=self.is_on_air:
								cb.config(text = "Запись активна                  " if var.get() else "Активировать запись видео")
								)

		self.is_audio_on_air = tk.BooleanVar()
		self.is_audio_on_air_widget_checkbox = tk.Checkbutton(
			self.app,
			text='Активировать запись аудио',
			bg=self.bg_color,
			selectcolor=self.bg_color,
			activebackground=self.accent_color,
			disabledforeground=self.accent_color,
			fg=self.alt_text_color,
			activeforeground='white',
			font=('Helvetica', 15),
			variable=self.is_audio_on_air,
			onvalue=1,
			offvalue=0,
			command=self.audio_processor.audio_relay
		)

		self.is_audio_on_air.trace_add('write', lambda *_, cb=self.is_audio_on_air_widget_checkbox, var=self.is_audio_on_air: 
									cb.config(fg=self.accent_color if var.get() else self.alt_text_color))
		self.is_audio_on_air.trace_add('write', lambda *_, cb=self.is_audio_on_air_widget_checkbox, var=self.is_audio_on_air:
								cb.config(text = "Микрофон активен             " if var.get() else "Активировать запись аудио"))


		self.camera_label = tk.Label(
        self.app,
        text="Выбор камеры:",
        bg=self.bg_color,
        fg=self.alt_text_color,
        font=('Helvetica', 12, 'bold')
    )
    
		self.microphone_label = tk.Label(
			self.app,
			text="Выбор микрофона:",
			bg=self.bg_color,
			fg=self.alt_text_color,
			font=('Helvetica', 12, 'bold')
		)

		self.voice_class_text = tk.Label(
			self.app,
			text='-',
			bg=self.bg_color,
			fg=self.accent_color,
			font=('Helvetica', 20, 'bold')
		)

		self.play_button = tk.Button(
			self.app,
			text="PAUSE",
			bg=self.accent_color,
			fg=self.text_color,
			activebackground=self.accent_color,
			activeforeground=self.text_color,
			font=('Helvetica', 25, 'bold'),
			relief='flat',
			borderwidth=0,
			command=self.change_vid_state
		)

		self.MainCanvas.create_window((20, 20), window=self.table, anchor=tk.NW, width=800, height=200)
		self.MainCanvas.create_window((840, 0), window=self.camera_label, anchor=tk.NW)
		self.MainCanvas.create_window((840, 30), window=self.cameras_list_widget, anchor=tk.NW)
		self.MainCanvas.create_window((840, 70), window=self.cam_recap_but_widget, anchor=tk.NW)
		self.MainCanvas.create_window((840, 110), window=self.cam_list_update_but_widget, anchor=tk.NW)
		self.MainCanvas.create_window((840, 150), window=self.is_on_air_widget_checkbox, anchor=tk.NW)
		self.MainCanvas.create_window((20, 280), window=self.return_but, anchor=tk.NW)
		self.MainCanvas.create_window((840, 190), window=self.is_audio_on_air_widget_checkbox, anchor=tk.NW)
		self.MainCanvas.create_window((1300, 290), window=self.play_button, anchor=tk.NW)
		self.MainCanvas.create_window((20, 250), window=self.voice_class_text, anchor=tk.NW)
		self.MainCanvas.create_window((1200, 0), window=self.microphone_label, anchor=tk.NW)
		self.MainCanvas.create_window((1200, 30), window=self.audio_list_widget, anchor = tk.NW)
		self.MainCanvas.create_window((1200, 70), window=self.spectrogram_label, anchor=tk.NW)
		self.refresh_voice_class("-")

		#self.play_sound_button_widget = ttk.Button(text = "Проиграть звук", command= self.audio_processor.play_sound)
		#self.play_sound_button_widget.pack()

		self.logging_thread_function()
		self.cv.open_camera()
		self.app.after(500, self.update_table)
		self.app.mainloop()

	def refresh_voice_class(self, class_voice):
		self.voice_class_text.config(text=f"Текущее настроение голоса: {class_voice}")

	
	def update_spectrogram(self, spectrogram_image):
		self.spectrogram_label.imgtk = spectrogram_image
		self.spectrogram_label.configure(image=spectrogram_image)
	
	def logging_thread_function(self):
		self.csv_logger.log_info("{"+f"face_emotion: {self.logged_face_emotion.get()}, pose_emotion: {self.logged_pose_emotion.get()}, voice_emotion: '{self.logged_voice_emotion.get()}', status: {self.dangerous_people_logs}, name: '{self.logged_name}', birthday: '{self.logged_date}'"+"}")
		self.process_log(f"Faces: {self.logged_face_emotion.get()}; Poses: {self.logged_pose_emotion.get()}; Voices: {self.logged_voice_emotion.get()}")
		self.app.after(300, self.logging_thread_function)
	def process_log(self, log_line):
		parts = log_line.split("; ")
		if len(parts) < 3:
			return

		faces_str = parts[0].split("Faces: ")[-1]
		poses_str = parts[1].split("Poses: ")[-1]
		voice_str = parts[2].split("Voices: ")[-1].strip().lower()

		faces = self.safe_eval(faces_str, {})
		poses = self.safe_eval(poses_str, {})

		voice_pos = 1 if voice_str in self.positive_emotions else 0
		voice_neg = 1 if voice_str in self.negative_emotions else 0

		all_ids = set(faces.keys()) | set(poses.keys())
		for person_id in all_ids:
			face_emotion = str(faces.get(person_id, '-')).lower()
			face_pos = 1 if face_emotion in self.positive_emotions else 0
			face_neg = 1 if face_emotion in self.negative_emotions else 0
			pose_emotion = str(poses.get(person_id, '-')).lower()
			pose_pos = 1 if pose_emotion in self.positive_emotions else 0
			pose_neg = 1 if pose_emotion in self.negative_emotions else 0

			total_pos = face_pos + pose_pos + voice_pos
			total_neg = face_neg + pose_neg + voice_neg
			total = total_pos + total_neg

			current = self.people_logs.get(person_id, (0, 0, 0))
			new_pos = current[0] + total_pos
			new_neg = current[1] + total_neg * 1000
			new_total = current[2] + total
			self.people_logs[person_id] = (new_pos, new_neg, new_total)
			if new_total >= 200 and new_neg > new_pos:
				self.dangerous_people_logs.add(person_id)

	def safe_eval(self, s, default):
		try:
			return eval(s.replace("'", "\""))
		except:
			return default
	
	def go_to_start(self):
		self.app.destroy()
		self.cv.vid.release()
		start_win()

	def update_table(self):
		self.table.delete(*self.table.get_children())
		
		# Получаем текущие данные о эмоциях
		faces = self.safe_eval(self.logged_face_emotion.get(), {})
		poses = self.safe_eval(self.logged_pose_emotion.get(), {})
		
		# Собираем все ID в кадре
		all_ids = set(faces.keys()) | set(poses.keys())
		
		for person_id in all_ids:
			face_emotion = faces.get(person_id, '-')
			pose_emotion = poses.get(person_id, '-')
			status = "ОПАСЕН" if person_id in self.dangerous_people_logs else "-"
			playsound("../assets/alarm_sound.mp3", False) if person_id in self.dangerous_people_logs else "-"

			tags = ('danger',) if status == "ОПАСЕН" else ()
			
			self.table.insert('', 'end', 
							values=(person_id, face_emotion, pose_emotion, status),
							tags=tags)
		
		self.app.after(500, self.update_table)

	def change_vid_state(self):
		if self.cv.is_video_on_air == False:
			self.cv.is_video_on_air = True
			self.cv.open_camera()
			self.play_button["text"] = "STOP"
		else:
			self.cv.is_video_on_air = False
			self.play_button["text"] = "PLAY"

	def go_to_start(self):
		self.app.destroy()
		self.cv.vid.release()
		start_win()

class start_win:
	def __init__(self):
		self.start_window = tk.Tk()
		self.start_window.configure(bg="#CDCDCD")
		self.start_window.title("VAN (Video Analytic Network)")
		print("OK STARTING")

		self.start_window.geometry("400x300")
		
		logos_frame = tk.Frame(self.start_window, bg = "#CDCDCD")
		logos_frame.pack(pady=20)
		data_logo_img = Image.open('./assets/data_kvantum_logo.png')
		data_logo_img = data_logo_img.resize((100, 100))
		self.data_photo_image = ImageTk.PhotoImage(data_logo_img)
		self.data_logo_widget = tk.Label(logos_frame, image=self.data_photo_image, bg="#CDCDCD")
		self.data_logo_widget.pack(side='left', padx=10)
		rzd_logo_img = Image.open('./assets/rzd_logo.png')
		rzd_logo_img = rzd_logo_img.resize((100, 100))
		self.rzd_photo_image = ImageTk.PhotoImage(rzd_logo_img)
		self.rzd_logo_widget = tk.Label(logos_frame, image=self.rzd_photo_image, bg="#CDCDCD")
		self.rzd_logo_widget.pack(side='left', padx=10)
		cont_logo_img = Image.open('./assets/contest_logo.png')
		cont_logo_img = cont_logo_img.resize((100, 100))
		self.cont_photo_image = ImageTk.PhotoImage(cont_logo_img)
		self.cont_logo_widget = tk.Label(logos_frame, image=self.cont_photo_image, bg="#CDCDCD")
		self.cont_logo_widget.pack(side='left', padx=10)
		
		self.authors = tk.Label(self.start_window, 
							text="Система распознавания эмоций VAN \n Разработано Дата Квантумом Кванториума СВДЖД \n Инструкции и информация: \n https://github.com/KTOTO9567578347/VAN/tree/master", 
							bg="#CDCDCD")
		self.authors.pack()
		start_but = ttk.Button(text='ЗАПУСК', master=self.start_window, command=lambda: self.start_main())
		start_but.pack(pady=20)
		self.start_window.mainloop()
	def start_main(self):
		self.start_window.destroy()
		main_win()