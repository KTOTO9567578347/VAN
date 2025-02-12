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

from interface import start_win

logging.basicConfig(filename="logs.txt",
                    filemode='a',
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

start_win()