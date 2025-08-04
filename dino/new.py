import cv2
import numpy as np
import pyautogui

while True:
    image = pyautogui.screenshot(region=(200,350,255,250))
    image = cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)

    black_p_c = np.sum(image < 100)
    white_p_c = np.sum(image > 100)

    if black_p_c > 4000 and black_p_c < 30000:
        pyautogui.press('up')

    if white_p_c > 4000 and white_p_c < 30000:
        pyautogui.press('up')    

    cv2.imshow('image', image)

    if cv2.waitKey(1) & 0xFF == ord('p'):
        print('Black pixel : ',black_p_c)
        print('White pixel : ',white_p_c)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break