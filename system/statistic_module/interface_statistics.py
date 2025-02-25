import tkinter as tk
from tkinter import ttk
from sqlite_api import SQLiteAPI  # Предполагается, что у вас есть этот модуль

class AdminPanelWindow:
    def __init__(self, username):
        self.sqlAPI = SQLiteAPI()
        self.win = tk.Toplevel()  # Создаем новое окно
        self.win.title("Админ-панель")
        self.win.bind('<Escape>', lambda e: self.win.quit()) 

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
        
        self.win.after(500, self.update_user_table)
        self.win.mainloop()

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