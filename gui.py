import os
import threading

import time
from datetime import datetime

import numpy as np

from PIL import Image
import cv2
from mss import mss

from pynput import mouse

import img2pdf
import glob

import PySimpleGUI as sg

# pyinstaller -F --noconsole -n Appname gui.py  

# LAYOUT
RED = "#f02828"
ORANGE = "#e0741f"
GREEN = "#08c65b"
WHITE = "#FFF"


layout = [
    [sg.Text("Name a new folder or select an existing folder:", key="titletext")],
    [
        sg.Input(f'Folder-{datetime.now().strftime("%d-%m-%Y-%H-%M-%S")}', key="foldername"), 
        sg.FolderBrowse()
    ],
    [sg.Text("Set positions...", size=(50, 0), key="positions_text")],
    [
        sg.Button("Positions", key="positions_button"), 
        sg.Button("Take Screenshot", key="take_screenshot", disabled=True),  
        sg.Button("Images to PDF", key="pdf_button")
    ],
    [
        sg.Button("Start Automatic Screenshots", key="auto_screenshot", disabled=True),
        sg.Button("Stop", key="stop_auto_screenshot", disabled=True),
    ],
    [sg.Button("Open Folder", key="open_folder")],
    [sg.Text("Waiting...", size=(30, 0), key="status")],
]

window = sg.Window(
    "App", 
    layout, 
    location=(100, 300),
    margins=(0, 0),
    no_titlebar=False, 
    alpha_channel=1, 
    grab_anywhere=True, 
    resizable=True, 
    finalize=True,
    )
    
# FUNCTIONS
positions = [0, 0, 0, 0]

def position_check(positions):
    top = positions[1]
    left = positions[0]
    width = positions[2] - positions[0]
    height = positions[3] - positions[1]
    return width > 0 and height > 0, top, left, width, height

def start_mouse():
    with mouse.Listener(on_click=start_on_click) as listener:
            listener.join()

def end_mouse():
    with mouse.Listener(on_click=end_on_click) as listener:
            listener.join()

def start_on_click(x, y, button, pressed):
    if pressed:
        positions[0] = x
        positions[1] = y
    else:
        return False

def end_on_click(x, y, button, pressed):
    if pressed:
        positions[2] = x
        positions[3] = y
    else:
        return False

# values["foldername"]
def save_screenshot(img):
    # create folder
    foldername = values["foldername"]
    if not os.path.exists(foldername):
        os.mkdir(foldername)

    # save image
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    Image.fromarray(img).save(f"{foldername}/img-{timestamp}.png")

sct = mss()
def take_screenshot(top, left, width, height):

    # take screenshot depending on the positions
    box = {"top": top, "left": left, "width": width, "height": height}
    img = cv2.cvtColor(np.array(sct.grab(box)), cv2.COLOR_RGB2BGR)
    
    save_screenshot(img)
    
def take_auto_screenshot(top, left, width, height):
    # take screenshot depending on the positions
    box = {"top": top, "left": left, "width": width, "height": height}
    img_1 = cv2.cvtColor(np.array(sct.grab(box)), cv2.COLOR_RGB2BGR)
    save_screenshot(img_1)
    while True and not e_threading.is_set():
        window.Refresh()
        e_threading.wait(2)
        img_2 = cv2.cvtColor(np.array(sct.grab(box)), cv2.COLOR_RGB2BGR)

        if not (img_1 == img_2).all():
            print("difference in images")
            save_screenshot(img_2)
            img_1 = img_2

            window["status"].Update(value="Screenshot taken!", text_color=GREEN)
            window.Refresh()
            time.sleep(1)
            window["status"].Update(value="Auto Screenshot started!", text_color=ORANGE)
            window.Refresh()

# RUNNING LOOP
while True:
    event, values = window.read(timeout=10)

    # position
    if event == "positions_button":
        time.sleep(0.1)
        window["positions_text"].Update(value="Select a top-left corner and then a bottom-right corner.", text_color=ORANGE)
        window.Refresh()

        start_mouse()
        end_mouse()

        if position_check(positions)[0]:
            window["positions_text"].Update(value="Positions set.", text_color=GREEN)
            window["take_screenshot"].Update(disabled=False)
            window["auto_screenshot"].Update(disabled=False)
            window.Refresh()
        else:
            window["positions_text"].Update(value="Positions not correct.", text_color=RED)
            window.Refresh()
            time.sleep(1)
            window["positions_text"].Update(value="Set positions...", text_color=WHITE)
            window.Refresh()

    # take screenshot
    if event == "take_screenshot":
        if position_check(positions)[0]:
            take_screenshot(
                top=position_check(positions)[1], 
                left=position_check(positions)[2], 
                width=position_check(positions)[3], 
                height=position_check(positions)[4]
            )

            window["status"].Update(value="Screenshot taken!", text_color=GREEN)
            window.Refresh()
            time.sleep(1)
            window["status"].Update(value="Waiting...", text_color=WHITE)
            window.Refresh()


    if event == "auto_screenshot":
        if position_check(positions)[0]:

            e_threading = threading.Event()
            t = threading.Thread(target=take_auto_screenshot, kwargs={
                "top": position_check(positions)[1],
                "left": position_check(positions)[2],
                "width": position_check(positions)[3],
                "height": position_check(positions)[4]})
            t.start()

            window["status"].Update(value="Auto Screenshot started!", text_color=ORANGE)
            window["auto_screenshot"].Update(disabled=True)
            window["stop_auto_screenshot"].Update(disabled=False)
            window.Refresh()
        else:
            window["status"].Update(value="No positions selected.", text_color=RED)
            window.Refresh()
            time.sleep(1)
            window["status"].Update(value="Waiting...", text_color=WHITE)
            window.Refresh()

    if event == "stop_auto_screenshot":
        e_threading.set()
        window["stop_auto_screenshot"].Update(disabled=True)
        window["auto_screenshot"].Update(disabled=False)
        window.Refresh()
        window["status"].Update(value="Auto Screenshot stopped", text_color=ORANGE)
        window.Refresh()
        time.sleep(1)
        window["status"].Update(value="Waiting...", text_color=WHITE)
        window.Refresh()

    # images to pdf
    if event == "pdf_button":
        foldername = values["foldername"]
        if os.path.exists(foldername):
            images = glob.glob(f"{foldername}/*.png")
            with open(f"{foldername}/{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}.pdf","wb") as f:
                f.write(img2pdf.convert(images))

            window.FindElement("status").Update(value="Creating PDF...", text_color=GREEN)
            window.Refresh()
            time.sleep(1)
            window.FindElement("status").Update(value="Waiting...", text_color=WHITE)
            window.Refresh()
        else:
            window.FindElement("status").Update(value="Folder doesn't exist or is empty.", text_color=RED)
            window.Refresh()
            time.sleep(1)
            window.FindElement("status").Update(value="Waiting...", text_color=WHITE)
            window.Refresh()

    if event == "open_folder":
        foldername = values["foldername"]
        if os.path.exists(foldername):
            folder = os.path.realpath(foldername)
            os.system(f"start {folder}")
        else:
            window.FindElement("status").Update(value="Folder doesn't exist.", text_color=RED)
            window.Refresh()
            time.sleep(1)
            window.FindElement("status").Update(value="Waiting...", text_color=WHITE)
            window.Refresh()

    # closing program
    if event is None or event == "Exit":
        break
window.Close()