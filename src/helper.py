import time
import pyclick
import pyautogui
from pynput.keyboard import Controller, KeyCode
import win32con

def move_to_songs():
    hc = pyclick.HumanClicker()
    hc.move((972, 532),  0)
    time.sleep(0.2)
    hc.click()
    time.sleep(0.2)
    hc.click()
    time.sleep(0.2)
    hc.click()
    time.sleep(0.2)
    hc.click()
    time.sleep(1)
    hc.move((1789, 88), 0)
    time.sleep(0.2)
    hc.click()
    time.sleep(0.2)
    del hc
    return

def find_maps(stars=1):
    c = Controller()
    search = f"stars>{stars}.01 stars<{stars}.99 mode=osu length>90"
    c.type("".join(map(lambda _: "\b", search)))
    time.sleep(0.2)
    c.type(search)

def launch_random_beatmap():
    time.sleep(0.5)
    c = Controller()
    hc = pyclick.HumanClicker()
    c.press(KeyCode.from_vk(win32con.VK_F2))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_F2))
    time.sleep(1)
    c.press(KeyCode.from_vk(win32con.VK_RETURN))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_RETURN))
    x, y = pyautogui.center((0, 0, 1920, 1080))
    hc.move((x, y),  0)
    del hc
    return

def reset_mods():
    time.sleep(0.5)
    c = Controller()
    c.press(KeyCode.from_vk(win32con.VK_F1))
    time.sleep(0.1)
    c.release(KeyCode.from_vk(win32con.VK_F1))
    time.sleep(0.1)
    c.press("1")
    time.sleep(0.1)
    c.release("1")
    c.press(KeyCode.from_vk(win32con.VK_ESCAPE))
    time.sleep(0.1)
    c.release(KeyCode.from_vk(win32con.VK_ESCAPE))
    return

def enable_mods(no_fail = True, hard_rock = False, double_time = False):
    time.sleep(0.5)
    c = Controller()
    c.press(KeyCode.from_vk(win32con.VK_F1))
    time.sleep(0.1)
    c.release(KeyCode.from_vk(win32con.VK_F1))
    time.sleep(0.1)
    
    if no_fail:
        c.press("w")
        time.sleep(0.1)
        c.release("w")
        time.sleep(0.1)
    if hard_rock:
        c.press("a")
        time.sleep(0.1)
        c.release("a")
        time.sleep(0.1)
    if double_time:
        c.press("d")
        time.sleep(0.1)
        c.release("d")
        time.sleep(0.1)
    
    c.press(KeyCode.from_vk(win32con.VK_ESCAPE))
    time.sleep(0.1)
    c.release(KeyCode.from_vk(win32con.VK_ESCAPE))
    return

def return_to_beatmaps():
    c = Controller()
    c.press(KeyCode.from_vk(win32con.VK_ESCAPE))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_ESCAPE))
    time.sleep(3)
    return
