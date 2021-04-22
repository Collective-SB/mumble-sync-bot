import pyautogui
import time
from pynput.keyboard import Listener

name = input(">")

def setWing():
    print(str(pyautogui.position()))
    pyautogui.hotkey("ctrl", "z")
    time.sleep(0.2)

    pyautogui.click(764, 392)
    time.sleep(0.1)
    pyautogui.click(965, 639)
    time.sleep(0.1)
    pyautogui.click(758, 790)
    time.sleep(0.1)
    pyautogui.press("backspace", 4)
    time.sleep(0.1)
    pyautogui.typewrite(name)
    pyautogui.press("enter")
    time.sleep(0.1)
    pyautogui.click(1318, 512)
    
    pyautogui.click(1193, 876)

def on_press(key):
    if str(key) == "'='":

        setWing()

def start():
    with Listener(on_press=on_press) as listener:
        listener.join()

start()