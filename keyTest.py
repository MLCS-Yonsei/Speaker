from pywinauto.application import Application
import pywinauto

import win32ui
import win32gui
import win32com.client

import serial
import serial.tools.list_ports

from bin.keys import Keys
from time import time, sleep

# Move to bottom of the menu
shell = win32com.client.Dispatch("WScript.Shell")
shell.SendKeys('%')

PyCWnd1 = win32ui.FindWindow( None, "Project CARS™" )
PyCWnd1.SetForegroundWindow()
PyCWnd1.SetFocus()

def keyPress(keys, key):
    keys.directKey(key)
    sleep(0.04)
    keys.directKey(key, keys.key_release)

keys = Keys()
keyPress(keys, "J")
keyPress(keys, "j")

for i in range(1,6):
    keyPress(keys, "UP")
    keyPress(keys, "LEFT")

keyPress(keys, "RETURN")
