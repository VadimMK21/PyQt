import cv2
import numpy as np
import pyautogui
import pytesseract
import time
import sys
from vidgear.gears import ScreenGear
#import pyscreenshot as ImageGrab
from PIL import ImageGrab

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

x1=320
y1=180

x2=1295
y2=905

x_gifts=1780
y_gifts=925

v=140
h=25

num_healing = 0
num_loading = 0

iterr = 5

config = r'--oem 3 --psm 10 lang="eng"' #Настройки конфигурации oem - версия движка psm - версия формата изображения

def healing():
    
    global iterr

    for _ in range(iterr):
        pyautogui.click(x=460, y=360)

def loading():
    
    pyautogui.click(x=x_gifts, y=y_gifts)
    pyautogui.click(x=x_gifts, y=y_gifts)

while True:

    score_h = ImageGrab.grab(bbox=(x1,y1,(v+x1),(h+y1)))
    score_g = ImageGrab.grab(bbox=(x2,y2,(v+x2),(h+y2)))

    text_health = pytesseract.image_to_string(score_h, config=config)#Распознаем текс с изображения
    health = text_health.split('/')
    bbrb = health[0]
    bbrb = bbrb.replace(" ","")    
 
    text_gifts = pytesseract.image_to_string(score_g, config=config)#Распознаем текс с изображения
    gifts = text_gifts.split('/')
    bbrb1 = gifts[0]
    bbrb1 = bbrb1.replace("(","")
    #print(bbrb1)
    #print(bbrb[:4])

    try:
        if int(bbrb[:4]) < 3500:
            healing()
            num_healing += 1
            print('healing - ', num_healing)
    except:
        print('error healing')
        #pass

    try:
        if int(bbrb1) >= 99:
            loading()
            num_loading += 1
            print('loading - ', num_loading)
    except:
        #print('error loading')
        pass
          
    time.sleep(0.2)