from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS

import json
from urllib.parse import urlparse

import atexit
import datetime
import time
import os

from pydub import AudioSegment
from pydub.playback import play
import pyaudio

import win32ui
import win32gui
import win32com.client

from pywinauto.application import Application
from pywinauto.keyboard import SendKeys

from bin.keys import Keys
from time import time, sleep

from math import log, ceil, floor
from polly import play_with_polly

import socket
HOST = '192.168.0.2'  
PORT = 65432

dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

def create_app():
    return app

app = create_app()  

@app.route('/status', methods=['GET'])
def status():
    return jsonify({}), 200

def make_chunks(audio_segment, chunk_length):
    """
    Breaks an AudioSegment into chunks that are <chunk_length> milliseconds
    long.
    if chunk_length is 50 then you'll get a list of 50 millisecond long audio
    segments back (except the last one, which can be shorter)
    """
    number_of_chunks = ceil(len(audio_segment) / float(chunk_length))
    return [audio_segment[i * chunk_length:(i + 1) * chunk_length]
            for i in range(int(number_of_chunks))]

@app.route('/play', methods=['GET'])
def play():
    req_path = request.args.get('path')
    speaker = request.args.get('speaker')

    if speaker == 'Jiwoong':
        audio_format = pyaudio.paInt16
    elif speaker == 'Ari':
        audio_format = pyaudio.paInt32
    elif speaker == 'Furby':
        audio_format = pyaudio.paInt16
    else:
        audio_format = pyaudio.paInt32

    # file_path = os.path.join(dir,'bin')
    file_path = dir
    for p in req_path.split('/'):
        if len(p) is not 0:
            file_path = os.path.join(file_path,p)

    seg = AudioSegment.from_wav(file_path)
    p = pyaudio.PyAudio()
    stream = p.open(format=audio_format,
                    channels=seg.channels,
                    rate=seg.frame_rate,
                    output=True)

    # break audio into half-second chunks (to allows keyboard interrupts)
    for chunk in make_chunks(seg, 500):
        stream.write(chunk._data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    # time.sleep(seg.duration_seconds)

    return jsonify({}), 200

def keyPress(keys, key):
    keys.directKey(key)
    sleep(0.04)
    keys.directKey(key, keys.key_release)

@app.route('/start', methods=['GET'])
def start():
    # Move to bottom of the menu
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    
    PyCWnd1 = win32ui.FindWindow( None, "Project CARS™" )
    PyCWnd1.SetForegroundWindow()
    PyCWnd1.SetFocus()
    
    keys = Keys()
    keyPress(keys, "J")
    keyPress(keys, "j")

    for i in range(1,4):
        keyPress(keys, "UP")
        keyPress(keys, "LEFT")
    keyPress(keys, "RETURN")
  
    return jsonify({}), 200

@app.route('/finish', methods=['GET'])
def finish():
    # Move to bottom of the menu
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    
    PyCWnd1 = win32ui.FindWindow( None, "Project CARS™" )
    PyCWnd1.SetForegroundWindow()
    PyCWnd1.SetFocus()
    
    keys = Keys()
    keyPress(keys, "R")
    keyPress(keys, "r")

    for i in range(1,4):
        keyPress(keys, "UP")

    keyPress(keys, "RETURN")
  
    return jsonify({}), 200

@app.route('/host_ready', methods=['GET'])
def host_ready(): 
    keys = Keys()
    keyPress(keys, "J")
    keyPress(keys, "j")

    for i in range(1,4):
        keyPress(keys, "UP")
        keyPress(keys, "RIGHT")

    keyPress(keys, "RETURN")
  
    return jsonify({}), 200

# @app.route('/host_start', methods=['GET'])
# def host_start():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind((HOST, PORT))
#     sock.listen()
#     conn, addr = sock.accept()
#     while True:
#         data = conn.recv(1024)
#         if data == b'\x00':
#             keys = Keys()
#             keyPress(keys, "J")
#             keyPress(keys, "j")

#             for i in range(1,6):
#                 keyPress(keys, "UP")
#                 keyPress(keys, "LEFT")

#             keyPress(keys, "RETURN")
#             break
  
#     return jsonify({}), 200

# @app.route('/guest_ready', methods=['GET'])
# def guest_ready(): 
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     while 1:
#         try:
#             sock.connect((HOST, PORT))
#             break
#         except:
#             continue
#     sock.sendall(bytes(1))
  
#     return jsonify({}), 200

@app.route('/car_position_reset', methods=['GET'])
def car_position_reset():
    # Move to bottom of the menu
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    
    PyCWnd1 = win32ui.FindWindow( None, "Project CARS™" )
    PyCWnd1.SetForegroundWindow()
    PyCWnd1.SetFocus()
    
    keys = Keys()

    keyPress(keys, "RETURN")
  
    return jsonify({}), 200

@app.route('/polly', methods=['GET'])
def polly():
    text = request.args.get('text')
    print("RCVD Text:",text)
    try:
        play_with_polly(text)
        
        return jsonify({'status':True}), 200
    except Exception as ex:
        return jsonify({'status':False,'msg':str(ex)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=3000)
