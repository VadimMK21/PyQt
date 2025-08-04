import cv2
import numpy as np
import pyautogui
import pytesseract
import time
import sys

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


x1=320
y1=180

x2=1295
y2=905

x_gifts=1780
y_gifts=925

v=140
h=25

config = r'--oem 3 --psm 10 lang="eng"' #Настройки конфигурации oem - версия движка psm - версия формата изображения

while True:
    score_h = pyautogui.screenshot(region=(x1,y1,v,h))
    score_g = pyautogui.screenshot(region=(x2,y2,v,h))
    #score1 = cv2.cvtColor(np.array(score_h),cv2.COLOR_RGB2BGR)
    #score2 = cv2.cvtColor(np.array(score_g),cv2.COLOR_RGB2BGR)


    text_health = pytesseract.image_to_string(score_h, config=config)#Распознаем текс с изображения
    health = text_health.split('/')
    bbrb = health[0]
    bbrb = bbrb.replace(" ","")    
    #print(bbrb[:4])

    text_gifts = pytesseract.image_to_string(score_g, config=config)#Распознаем текс с изображения
    gifts = text_gifts.split('/')
    bbrb1 = gifts[0]
    bbrb1 = bbrb1.replace("(","")    
    print(bbrb1)
    print(bbrb[:4])

    try:
        if int(bbrb[:4]) < 3700:
            print('hiling')
            pyautogui.click(x=460, y=360)
            pyautogui.click(x=460, y=360)
            pyautogui.click(x=460, y=360)
            pyautogui.click(x=460, y=360)

        if int(bbrb1) >= 99:
            print('gifts')
            pyautogui.click(x=x_gifts, y=y_gifts)
            pyautogui.click(x=x_gifts, y=y_gifts)
    except:
        print('error')

    #cv2.imshow('score',score2)
                
    if cv2.waitKey(25) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
            
    time.sleep(0.5)