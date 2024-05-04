# Done by Frannecklp
import cv2
import numpy as np
from win32 import win32gui, win32api
import win32ui, win32con
import mouse
from constants import SCREEN_HEIGHT, SCREEN_WIDTH

class Environment:
    @staticmethod
    def grabScreen(region=None):
        hwin = win32gui.GetDesktopWindow()
        if region:
                left,top,x2,y2 = region
                width = x2 + 1
                height = y2 + 1
        else:
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

        signedIntsArray = bmp.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (height,width,4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())
        
        grayed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(grayed, (260, 202))
        output = np.expand_dims(np.asarray(resized) / 255, axis=-1)

        return output, resized
    @staticmethod
    def grabMousePosition():
        x, y = win32api.GetCursorPos()
        return np.asarray([x / SCREEN_WIDTH, y / SCREEN_HEIGHT])
    @staticmethod
    def getMousePressState():
        return np.asarray([int(mouse.is_pressed())])
    
    @staticmethod
    def step(actions):
        x, y, click = actions
        xx, yy = win32api.GetCursorPos()
        
        x *= 50
        y *= 50
        
        if (xx + x > 1610 or xx + x < 310):
            x = 0
        if (yy + y > 1045 or yy + y < 35):
            y = 0
            
        mouse.move(xx + x, yy + y)
        
        if (click < -0.5):
            mouse.release()
        if (click > 0.5):
            mouse.press()
    
    # (-inf; +inf) - dx

    # (-inf; +inf) - dy

    # (-inf, -0.5) - release
    # [-0.5, 0.5] - do nothing
    # (0.5, +inf) - press