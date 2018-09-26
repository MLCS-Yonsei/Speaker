from pywinauto.application import Application
import pywinauto

import win32ui
import win32gui
import win32com.client

import serial
import serial.tools.list_ports

# from utils import send_crest_requset
import multiprocessing as mp
import time
import json

import redis
import socket

from utils.keys import Keys

# Move to bottom of the menu
shell = win32com.client.Dispatch("WScript.Shell")
shell.SendKeys('%')

PyCWnd1 = win32ui.FindWindow( None, "Project CARS™" )
PyCWnd1.SetForegroundWindow()
PyCWnd1.SetFocus()

keys = Keys()
keys.directKey("J")
keys.directKey("j")

for i in range(1,6):
    keys.directKey("UP")
    keys.directKey("LEFT")

keys.directKey("RETURN")
