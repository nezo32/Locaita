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
    search = f"stars>{stars}.01 stars<{stars}.99 mode=osu length>90 length<180"
    c.type("".join(map(lambda _: "\b", search)))
    time.sleep(0.2)
    c.type(search)
    
def skip_map_begining():
    c = Controller()
    c.press(KeyCode.from_vk(win32con.VK_SPACE))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_SPACE))
    return

def launch_random_beatmap():
    time.sleep(0.5)
    c = Controller()
    c.press(KeyCode.from_vk(win32con.VK_F2))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_F2))
    time.sleep(1)
    c.press(KeyCode.from_vk(win32con.VK_RETURN))
    time.sleep(0.2)
    c.release(KeyCode.from_vk(win32con.VK_RETURN))
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
        time.sleep(0.2)
        c.release("w")
        time.sleep(0.2)
    if hard_rock:
        c.press("a")
        time.sleep(0.2)
        c.release("a")
        time.sleep(0.2)
    if double_time:
        c.press("d")
        time.sleep(0.2)
        c.release("d")
        time.sleep(0.2)
    
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
