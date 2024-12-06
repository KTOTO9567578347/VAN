#загрузка библиотек
from PIL import Image, ImageTk #встроенный пакет для создания UI
import tkinter as tk
from tkinter import ttk
import datetime
from ultralytics import YOLO #API для упрощения загрузки и развертывания моделей
import cv2
from pygrabber.dshow_graph import FilterGraph #для обнаружения камер
from sys import exit
import logging

#настроим логирование
vid_save_path = "."
logging.basicConfig(filename="logs.txt",
                    filemode='a',
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

#модель для поиска лиц
class face_model:
	def __init__(self):
		self.model = YOLO('detect_face_model.pt')
	def detectMultiScale(self, frame):
		dat = []
		for res in self.model.predict(frame, verbose=False):
			for box in res.boxes:
				x, y, w, h = map(int, box.xywh.tolist()[0])
				dat.append([x - w//2, y - h//2, w, h])
		return dat

#класс для классификации эмоций
class CV:
	def __init__(self, output_app):
		self.app = output_app
		self.resolution = 96
		self.usable_model = YOLO(r"./best.pt")
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
	
	def open_camera(self): #открыть выбранную пользователем камеру
		ret, frame = self.vid.read()
		if (not ret or type(frame) == None):
			self.vid.release()
			print("NOVIDEO")
			frame = cv2.imread(r"./assets/nosignal.jpg")
		else:
			finded_faces = self.face_model.detectMultiScale(frame)
			predicted_classes = []
			for (x, y, w, h) in finded_faces:
				try:
					subframe = frame[x:x+w, y:y+h]
					subframe = cv2.resize(subframe, (self.resolution, self.resolution))
					prediction = self.usable_model.predict(subframe, verbose = False)[0]
					pred_id = prediction.probs.top1
					predicted_class = self.usable_model.names[pred_id]
					cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,0),2)
					cv2.putText(frame, self.rus_names[predicted_class], (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 255, 0))
					predicted_classes.append(predicted_class)
				except:
					pass
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

	def get_available_cameras(self): #получить список доступных камер
		devices = FilterGraph().get_input_devices()
		available_cameras = {}
		for device_index, device_name in enumerate(devices):
			available_cameras[device_index] = device_name
		return available_cameras
	
	def update_camera_list(self): #обновить список доступных камер
		cur_cam_list =  self.get_available_cameras()
		self.app.cameras_list_widget['value'] = [str(' '.join([str(key), cur_cam_list[key]])) for key in cur_cam_list.keys()]

	def recap_camera(self): #перезахват видеопотока на новую камеру
		global vid
		cur_cam = int(self.app.selected_camera.get().split()[0])
		print(cur_cam, " recapped")
		self.vid = cv2.VideoCapture(cur_cam, cv2.CAP_DSHOW)

	def start_record(self): #начать запись видео
		if (self.app.is_on_air.get()):
			vid_save_name = self.get_vid_save_name()
			print("start recording of ", vid_save_name)
			self.out = cv2.VideoWriter(vid_save_name, self.fourcc, self.video_write_FPS, (640, 480))
		else:
			print("End recording...")
			self.out.release()

class main_win: #класс интерфейса
	def __init__(self):
		self.cv = CV(self)
		self.app = tk.Tk()
		self.detected_emotion = tk.StringVar()
		self.app.bind('<Escape>', lambda e: self.app.quit()) 
		self.image_widget = tk.Label(self.app) 
		self.image_widget.pack() 
		
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

		self.logging_thread_function()
		self.cv.open_camera()
		self.app.mainloop()
	
	def logging_thread_function(self):
		logging.info(self.detected_emotion.get())
		self.app.after(30, self.logging_thread_function)
	
	def go_to_start(self):
		self.app.destroy()
		self.cv.vid.release()
		start_win()

class start_win: #класс стартового окна
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




start_win()
