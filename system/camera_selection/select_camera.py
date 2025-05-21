import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
from typing import List, Dict, Optional
from camera_selection.json_api import JsonAPI

class CameraManagerApp:
    def __init__(self, main_app):
        self.root = tk.Canvas(main_app)
        self.root.title("Менеджер камер")
        self.root.geometry("800x600")
        
        self.api = JsonAPI()
        
        # Стили
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        
        # Основные фреймы
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Таблица камер
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            self.tree_frame, 
            columns=("address", "status", "actions"), 
            show="headings",
            selectmode="browse"
        )
        
        self.tree.heading("address", text="Адрес камеры")
        self.tree.heading("status", text="Статус")
        self.tree.heading("actions", text="Действия")
        
        self.tree.column("address", width=300)
        self.tree.column("status", width=200)
        self.tree.column("actions", width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Панель управления
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self.add_frame = ttk.Frame(self.control_frame)
        self.add_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(self.add_frame, text="Добавить камеру:").pack(anchor=tk.W)
        
        self.camera_address = ttk.Entry(self.add_frame, width=40)
        self.camera_address.pack(side=tk.LEFT, padx=5)
        
        self.add_btn = ttk.Button(
            self.add_frame, 
            text="Добавить", 
            command=self.add_camera
        )
        self.add_btn.pack(side=tk.LEFT)
        
        # Кнопки управления
        self.btn_frame = ttk.Frame(self.control_frame)
        self.btn_frame.pack(side=tk.RIGHT)
        
        self.select_btn = ttk.Button(
            self.btn_frame,
            text="Выбрать",
            command=self.select_camera
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(
            self.btn_frame,
            text="Обновить",
            command=self.refresh_table
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Обновляем таблицу при запуске
        self.refresh_table()
        self.update_status()
    
    def refresh_table(self):
        """Обновляет таблицу камер"""
        self.tree.delete(*self.tree.get_children())
        cameras = self.api.get_cameras()
        selected_camera = self.api.get_selected()
        
        for cam in cameras:
            address = cam["address"]
            status = cam.get("status", "N/A")
            is_selected = "(Выбрана)" if address == selected_camera else ""
            
            self.tree.insert(
                "", 
                tk.END, 
                values=(address, status + is_selected, "Удалить")
            )
        
        # Привязываем двойной клик для выбора
        self.tree.bind("<Double-1>", self.on_double_click)
    
    def add_camera(self):
        """Добавляет новую камеру"""
        address = self.camera_address.get().strip()
        if not address:
            messagebox.showwarning("Ошибка", "Введите адрес камеры")
            return
        
        if self.api.add_camera(address):
            self.refresh_table()
            self.camera_address.delete(0, tk.END)
            self.status_var.set(f"Камера {address} добавлена")
        else:
            messagebox.showwarning("Ошибка", "Камера с таким адресом уже существует")
    
    def select_camera(self):
        """Выбирает камеру из таблицы"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите камеру из таблицы")
            return
        
        address = self.tree.item(selected_item)["values"][0]
        self.api.select_camera(address)
        self.refresh_table()
        self.status_var.set(f"Камера {address} выбрана")
    
    def delete_camera(self, address):
        """Удаляет камеру"""
        if messagebox.askyesno("Подтверждение", f"Удалить камеру {address}?"):
            if self.api.delete_camera(address):
                self.refresh_table()
                self.status_var.set(f"Камера {address} удалена")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить камеру")
    
    def on_double_click(self, event):
        """Обработчик двойного клика"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.selection()[0]
            address = self.tree.item(item)["values"][0]
            
            if column == "#3":  # Колонка "Действия"
                self.delete_camera(address)
            else:
                self.api.select_camera(address)
                self.refresh_table()
                self.status_var.set(f"Камера {address} выбрана")
    
    def update_status(self):
        """Обновляет статус бар"""
        cameras = self.api.get_cameras()
        selected = self.api.get_selected()
        status = f"Всего камер: {len(cameras)} | "
        status += f"Выбранная: {selected}" if selected else "Нет выбранной камеры"
        self.status_var.set(status)

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraManagerApp(root)
    root.mainloop()