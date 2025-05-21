import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
from typing import List, Dict, Optional

# Класс JsonAPI (немного доработанный)
class JsonAPI:
    def __init__(self, JSON_path: str = "cameras.json"):
        self.JSON_path = JSON_path
        if not os.path.exists(self.JSON_path):
            with open(self.JSON_path, 'w') as f:
                json.dump({"cameras": [], "selected": None}, f, indent=4)
    
    def _read_data(self) -> Dict:
        with open(self.JSON_path, 'r') as f:
            return json.load(f)
    
    def _write_data(self, data: Dict) -> None:
        with open(self.JSON_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def add_camera(self, address: str) -> bool:
        data = self._read_data()
        if address not in [cam["address"] for cam in data["cameras"]]:
            data["cameras"].append({"address": address, "status": "disconnected"})
            self._write_data(data)
            return True
        return False
    
    def select_camera(self, address: Optional[str]) -> None:
        data = self._read_data()
        data["selected"] = address
        self._write_data(data)
    
    def delete_camera(self, address: str) -> bool:
        data = self._read_data()
        initial_count = len(data["cameras"])
        data["cameras"] = [cam for cam in data["cameras"] if cam["address"] != address]
        if data["selected"] == address:
            data["selected"] = None
        self._write_data(data)
        return len(data["cameras"]) < initial_count
    
    def get_cameras(self) -> List[Dict]:
        return self._read_data()["cameras"]
    
    def get_selected(self) -> Optional[str]:
        return self._read_data()["selected"]
