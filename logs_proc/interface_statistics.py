import tkinter as tk
from tkinter import ttk
from sqlite_api import SQLiteAPI  # Предполагается, что у вас есть этот модуль

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

from ast import literal_eval
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class AdminPanelWindow:
    def __init__(self, username):
        c_font = TTFont('Arial', "./arialmt.ttf")
        pdfmetrics.registerFont(c_font)
        self.data = pd.DataFrame()
        self.sqlAPI = SQLiteAPI()
        self.win = tk.Toplevel()  # Создаем новое окно
        self.win.title("Админ-панель")
        self.win.bind('<Escape>', lambda e: self.win.quit()) 

        self.template_var = tk.StringVar()
        self.template_var.set("Шаблон 1")
        self.params = {
            "time": tk.BooleanVar(value=True),
            "id": tk.BooleanVar(value=True),
            "emotion_face": tk.BooleanVar(value=True),
            "emotion_pose": tk.BooleanVar(value=True),
            "emotion_voice": tk.BooleanVar(value=True),
            "system_verdict": tk.BooleanVar(value=True),
            "name": tk.BooleanVar(value=True),
            "birthday": tk.BooleanVar(value=True),
        }

        self.main_canvas = tk.Canvas(master = self.win, height=700, width=1200)
        self.main_canvas.pack(anchor=tk.CENTER, expand=True)

        # Заголовок с приветствием
        self.welcome_label = tk.Label(self.win, text=f"Добро пожаловать, {username}!")
        self.main_canvas.create_window((10, 10), window= self.welcome_label, anchor=tk.NW)

        # Заголовок с таблицы
        self.welcome_label = tk.Label(self.win, text=f"Таблица пользователей")
        self.main_canvas.create_window((250, 30), window= self.welcome_label, anchor=tk.NW)

        # Пример содержимого админ-панели
        self.table_columns = ('username', 'role', "Удалить?")
        self.user_table = ttk.Treeview(self.win, columns= self.table_columns, show = 'headings')
        self.user_table.heading('username', text = 'Пользователь')
        self.user_table.heading('role', text = 'Роль')
        self.user_table.bind("<Button-1>", self.on_table_click)
        self.main_canvas.create_window((10, 60), window= self.user_table, anchor=tk.NW)

        self.label_user_reg = tk.Label(self.win, text=f"Добавление пользователя:")
        self.main_canvas.create_window((10, 300), window= self.label_user_reg, anchor=tk.NW)

        self.username_reg_title = tk.Label(self.win, text=f"Логин:")
        self.main_canvas.create_window((10, 330), window= self.username_reg_title, anchor=tk.NW)

        self.password_reg_title = tk.Label(self.win, text=f"Пароль:")
        self.main_canvas.create_window((90, 330), window= self.password_reg_title, anchor=tk.NW)

        self.username_reg = tk.Text(self.win)
        self.main_canvas.create_window((10, 360), window= self.username_reg, anchor=tk.NW, width=60, height=20)

        self.password_reg = tk.Text(self.win)
        self.main_canvas.create_window((90, 360), window= self.password_reg, anchor=tk.NW, width=60, height=20)

        self.reg_user_but = tk.Button(self.win, text="Добавить пользователя", command=self.reg_new_user)
        self.main_canvas.create_window((10, 390), window= self.reg_user_but, anchor=tk.NW)

        self.welcome_label = tk.Label(self.win, text=f"Настройки логирования и создания отчётов")
        self.main_canvas.create_window((750, 30), window= self.welcome_label, anchor=tk.NW)

        # Выбор шаблона
        self.pattern_label = ttk.Label(self.win, text="Выберите шаблон:")
        self.main_canvas.create_window((750, 60), window=self.pattern_label, anchor=tk.NW)

        self.pattern_combobox = ttk.Combobox(self.win, textvariable=self.template_var, values=["Шаблон 1", "Шаблон 2"])
        self.main_canvas.create_window((750, 90), window=self.pattern_combobox, anchor=tk.NW)

        # Выбор параметров
        self.params_label = ttk.Label(self.win, text="Выберите параметры:")
        self.main_canvas.create_window((750, 120), window=self.params_label, anchor=tk.NW)
        row = 0
        for param, var in self.params.items():
            but = ttk.Checkbutton(self.win, text=param, variable=var)
            self.main_canvas.create_window((750, 140 + row * 20), window=but, anchor=tk.NW)
            row += 1
        
        self.gen_csv_but = ttk.Button(self.win, text="Загрузить CSV", command=self.load_csv)
        self.main_canvas.create_window((750, 300), window=self.gen_csv_but, anchor=tk.NW)

        self.gen_ans_but = ttk.Button(self.win, text="Сгенерировать отчет", command=self.generate_report)
        self.main_canvas.create_window((750, 330), window=self.gen_ans_but, anchor=tk.NW)

        self.save_template_but = ttk.Button(self.win, text="Сохранить шаблон", command=self.save_template)
        self.main_canvas.create_window((750, 360), window=self.save_template_but, anchor=tk.NW)

        self.watch_ans_but = ttk.Button(self.win, text="Просмотреть отчет", command=self.preview_report)
        self.main_canvas.create_window((750, 390), window=self.watch_ans_but, anchor=tk.NW)

        self.PDF_export_but = ttk.Button(self.win, text="Экспорт в PDF", command=self.export_to_pdf)
        self.main_canvas.create_window((750, 420), window=self.PDF_export_but, anchor=tk.NW)

        self.change_order_but = ttk.Button(self.win, text="Изменить порядок столбцов", command=self.change_column_order)    
        self.main_canvas.create_window((750, 450), window=self.change_order_but, anchor=tk.NW)

        #self.csv_table_title = tk.Label(self.win, text=f"Путь к экспортируемым логам")
        #self.main_canvas.create_window((700, 60), window= self.csv_table_title, anchor=tk.NW)

        #self.csv_table_filename = tk.Text(self.win)
        #self.main_canvas.create_window((900, 60), window= self.csv_table_filename, anchor=tk.NW, width=200, height=20)

        #self.import_csv_button = tk.Button(self.win, text="Импорт")
        #self.main_canvas.create_window((1050, 60), window = self.import_csv_button, anchor = tk.NW)

        self.csv_export_but = ttk.Button(self.win, text="Экспорт в CSV", command=self.export_to_csv)
        self.main_canvas.create_window((750, 480), window=self.csv_export_but, anchor=tk.NW)

        self.name_find_but = ttk.Button(self.win, text="Поиск в отчёте", command=self.get_search_res)
        self.main_canvas.create_window((750, 600), window=self.name_find_but, anchor=tk.NW)

        self.name_find_text = tk.Text(self.win)
        self.main_canvas.create_window((850, 600), window=self.name_find_text, anchor=tk.NW, width=100, height=20)

        self.win.after(500, self.update_user_table)
        self.win.mainloop()
    def name_search(self, zapr): 
        self.finded = pd.DataFrame(self.data[self.report_df['name'].str.contains(f"{zapr}.*")])


    def csv_to_pdf(self, data_frame, output_pdf):
        # Read CSV file using pandas

        # Convert dataframe to list and add the header
        data = [data_frame.columns.to_list()] + data_frame.values.tolist()

        # Create a new PDF with Reportlab
        pdf = SimpleDocTemplate(output_pdf, pagesize=landscape(letter))
        # Create a table with the data
        table = Table(data)
        # Add some style to the table (borders, background, etc.)
        style = TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Arial'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        # Add the table to the PDF
        pdf.build([table])
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.df = pd.read_csv(file_path, on_bad_lines='skip', sep = ";")
            time = self.df['Timestamp']

            for i in range(1,len(self.df)):
                mes = self.df['Message'].iloc[i].replace("face_emotion:", "'face_emotion':") \
                         .replace("pose_emotion:", "'pose_emotion':") \
                         .replace("voice_emotion:", "'voice_emotion':") \
                         .replace("'voice_emotion': ,", "'voice_emotion': None,") \
                         .replace("status:", "'status':") \
                         .replace("name:","'name':") \
                         .replace("birthday:", "'birthday':")
                print(mes)
                mes = literal_eval(mes)
                rows = []
                for index in mes['pose_emotion'].keys():
                    row = {
                        'time': time.iloc[i][:-4], 
                        'id': index,
                        'emotion_face': mes['face_emotion'].get(index),
                        'emotion_pose': mes['pose_emotion'].get(index),
                        'emotion_voice': mes['voice_emotion'],
                        'system_verdict': mes['status'],
                        'name': mes['name'],
                        'birthday': mes['birthday']
                    }
                    rows.append(row)
                ldf = pd.DataFrame(rows)
                self.data = pd.concat([self.data,ldf], ignore_index=True)
            self.df = self.data
            
            messagebox.showinfo("Успех", "CSV файл успешно загружен!")

    

    def generate_report(self):
        print(self.df)
        if not hasattr(self, 'df'):
            messagebox.showerror("Ошибка", "Сначала загрузите CSV файл!")
            return
        
        selected_params = [param for param, var in self.params.items() if var.get()]
        self.report_df = self.df[selected_params]
        messagebox.showinfo("Успех", "Отчет успешно сгенерирован!")
    
    def save_template(self):
        selected_params = [param for param, var in self.params.items() if var.get()]
        with open("template.txt", "w") as f:
            f.write("\n".join(selected_params))
        messagebox.showinfo("Успех", "Шаблон успешно сохранен!")
    
    def preview_report(self):
        if not hasattr(self, 'report_df'):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте отчет!")
            return
        
        preview_window = tk.Toplevel(self.win)
        preview_window.title("Предварительный просмотр отчета")
        text = tk.Text(preview_window)
        text.insert(tk.END, self.report_df.to_string())
        text.pack()

    def get_search_res(self):
        if not hasattr(self, "report_df"):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте отчет!")
            return
        
        self.name_search(zapr = self.name_find_text.get("1.0", "end-1c"))

        preview_window = tk.Toplevel(self.win)
        preview_window.title("Результаты поиска")
        text = tk.Text(preview_window)
        text.insert(tk.END, self.finded.to_string())
        text.pack()
    
    def export_to_csv(self):
        if not hasattr(self, 'report_df'):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте отчет!")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.report_df.to_csv(file_path)
            messagebox.showinfo("Успех", "Отчет успешно экспортирован в CSV!")

    def export_to_pdf(self):
        if not hasattr(self, 'report_df'):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте отчет!")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.csv_to_pdf(self.data, file_path)
            messagebox.showinfo("Успех", "Отчет успешно экспортирован в PDF!")
    
    def change_column_order(self):
        if not hasattr(self, 'report_df'):
            messagebox.showerror("Ошибка", "Сначала сгенерируйте отчет!")
            return
        
        order_window = tk.Toplevel(self.win)
        order_window.title("Изменение порядка столбцов")
        
        columns = list(self.report_df.columns)
        listbox = tk.Listbox(order_window, selectmode=tk.EXTENDED)
        for col in columns:
            listbox.insert(tk.END, col)
        listbox.pack()
        
        def update_order():
            selected_cols = [listbox.get(i) for i in listbox.curselection()]
            self.report_df = self.report_df[selected_cols]
            messagebox.showinfo("Успех", "Порядок столбцов успешно изменен!")
            order_window.destroy()
        
        ttk.Button(order_window, text="Применить", command=update_order).pack()
    
    def reg_new_user(self):
        username = self.username_reg.get("1.0", tk.END).rstrip()
        password = self.password_reg.get("1.0", tk.END).rstrip()
        self.sqlAPI.add_user(username, password, "user")
    
    def on_table_click(self, event):
        item = self.user_table.identify_row(event.y)
        column = self.user_table.identify_column(event.x)

        name, role, _ = self.user_table.item(item, 'values')
        if str(column) == "#3":
            self.sqlAPI.delete_user_by_username(name)

    def update_user_table(self):
        self.user_table.delete(*self.user_table.get_children())
        for item in self.sqlAPI.get_users():
            name, priveleges = item
            self.user_table.insert('', 'end', values=(name, priveleges, "🗑"))
        self.win.after(500, self.update_user_table)

class AdminLoginWindow:
    def __init__(self):
        self.sqlAPI = SQLiteAPI()

        self.win = tk.Tk()
        self.win.title("Авторизация в админ-панели")

        # Заголовок окна 🗑
        self.win_title = tk.Label(self.win, text="Авторизация в админ-панели.")
        self.win_title.pack(anchor=tk.CENTER)

        # Поле для ввода имени пользователя
        self.username_title = tk.Label(self.win, text="Имя пользователя")
        self.username_title.pack(anchor=tk.CENTER)
        self.username_string = tk.StringVar()
        self.username_widget = tk.Entry(self.win, textvariable=self.username_string)
        self.username_widget.pack(anchor=tk.CENTER)

        # Поле для ввода пароля
        self.password_title = tk.Label(self.win, text="Пароль")
        self.password_title.pack(anchor=tk.CENTER)
        self.password_string = tk.StringVar()
        self.password_widget = tk.Entry(self.win, textvariable=self.password_string, show="*")  # Скрываем пароль
        self.password_widget.pack(anchor=tk.CENTER)

        # Кнопка входа
        self.log_button = tk.Button(self.win, text="Войти", command=self.login)
        self.log_button.pack(anchor=tk.CENTER, pady=10)

        # Метка для вывода сообщений об ошибках
        self.error_label = tk.Label(self.win, text="", fg="red")
        self.error_label.pack(anchor=tk.CENTER)

        self.win.mainloop()

    def login(self):
        username = self.username_string.get()
        password = self.password_string.get()

        if self.sqlAPI.login(username, password):
            self.error_label.config(text="")  # Очищаем сообщение об ошибке
            self.win.withdraw()  # Скрываем текущее окно
            AdminPanelWindow(username)  # Открываем новое окно админ-панели
        else:
            self.error_label.config(text="Неверное имя пользователя или пароль")  # Показываем ошибку

# Запуск приложения
if __name__ == "__main__":
    AdminLoginWindow()