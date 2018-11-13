from pydub import AudioSegment
from pydub.playback import play
import pyaudio

import requests

import csv
import random

import time
import os

from math import log, ceil, floor
dir = os.path.dirname(os.path.abspath(__file__))

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

class audioPlayer():
    def __init__(self, target_ip):
        # self.method = getattr(self, result['flag'], lambda: "nothing")

        # data = result['data']
        self.target_ip = target_ip
        if self.target_ip == 'localhost':
            self.network_flag = False
        else:
            self.network_flag = True
        self.fast = 1
        self.audio_path = './bin/audio/'
        self.prev_file = None
        # self.method()
        with open('./bin/audio/index.csv', 'r') as csvfile:
            files = list(csv.DictReader(csvfile, delimiter=","))
            dicts = [dict(_) for _ in files]

        self.audio_files = dicts

    def playFile(self, file_path):
        print("Playing...",file_path, self.target_ip)

        speaker = list(filter(lambda af: af['file_name'] == file_path, self.audio_files))[0]['speaker']

        if speaker == 'Jiwoong':
            audio_format = pyaudio.paInt16
        elif speaker == 'Ari':
            audio_format = pyaudio.paInt32
        elif speaker == 'Furby':
            audio_format = pyaudio.paInt32
        else:
            audio_format = pyaudio.paInt32

        file_path = self.audio_path + str(file_path)
        if self.network_flag:
            
            # sound = AudioSegment.from_wav(dir + file_path)
            url = 'http://' + self.target_ip.split(':')[0] + ':3000/play?path=' + file_path + '&speaker=' + speaker
            r = requests.get(url)
            # time.sleep(sound.duration_seconds)
        else:
            seg = AudioSegment.from_wav(file_path)
            p = pyaudio.PyAudio()

            stream = p.open(format=audio_format,
                            channels=seg.channels,
                            rate=int(seg.frame_rate * self.fast),
                            output=True)

            # break audio into half-second chunks (to allows keyboard interrupts)
            for chunk in make_chunks(seg, 500):
                stream.write(chunk._data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            # time.sleep(sound.duration_seconds)

    def play(self, data, s_type, gender, target=''):
        method = getattr(self, data['flag'], lambda: "nothing")
        # print(gender)
        speaker = None
        if s_type == 'HFNV':
            speaker = 'Ari_half'
        elif s_type == 'BR':
            speaker = 'Furby'
        else:
            if gender == 'M':
                speaker = 'Jiwoong'
            elif gender == 'F':
                speaker = 'Ari'
        
        if speaker is not None:
            method(data['data'], s_type, speaker, target)
        else:
            print("ERROR : audioPlayer.py : play", data['data'], s_type, target)

    def overtake(self, data, s_type, speaker='', target=''):
        status = data['status']

        if status:
            # 추월함
            audio_files = list(filter(lambda af: af['category1'] == 'OT' and af['category2'] == 'S' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
            
        else:
            # 추월당함
            audio_files = list(filter(lambda af: af['category1'] == 'OT' and af['category2'] == 'F' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
    
        audio_file = random.choice(audio_files)
        if audio_file['file_name'] != self.prev_file:
            print(audio_file['file_name'],self.prev_file)
            self.playFile(audio_file['file_name'])
            self.prev_file = audio_file['file_name']


    def chase(self, data, s_type, speaker='', target=''):
        chase = data['chasing']
        acc = data['acc']
        alone = data['alone']
        rank = data['rank']

        if alone:
            if rank == 1:
                # 앞선 독주
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'AL1' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

            elif rank > 1:
                # 뒤쳐진 독주
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'AL2' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        else:
            if chase and acc:
                # 잘쫓아감
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'CS' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
                
            elif chase and (not acc):
                # 잘못쫓아감
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'CF' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

            elif (not chase) and acc:
                # 잘도망감
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'RS' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

            elif (not chase) and (not acc):
                # 잘못도망감
                audio_files = list(filter(lambda af: af['category1'] == 'CS' and af['category2'] == 'RF' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        audio_file = random.choice(audio_files)
        if audio_file['file_name'] != self.prev_file:
            print(audio_file['file_name'],self.prev_file)
            self.playFile(audio_file['file_name'])
            self.prev_file = audio_file['file_name']

    def collision(self, data, s_type, speaker='', target=''):
        crash_state = data['crash_state']
        print("Coll ", crash_state)
        if crash_state == 1:
            # 충격 Lv.1
            audio_files = list(filter(lambda af: af['category1'] == 'CO' and af['category2'] == 'D1' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
            
        elif crash_state == 2:
            # 충격 Lv.2
            audio_files = list(filter(lambda af: af['category1'] == 'CO' and af['category2'] == 'D2' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif crash_state >= 3:
            # 충격 Lv.3
            audio_files = list(filter(lambda af: af['category1'] == 'CO' and af['category2'] == 'D3' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        else:
            audio_files = []

        if len(audio_files) > 0:
            print("AP : Collision")
            audio_file = random.choice(audio_files)
            if audio_file['file_name'] != self.prev_file:
                print(audio_file['file_name'],self.prev_file)
                self.playFile(audio_file['file_name'])
                self.prev_file = audio_file['file_name']

    def random(self, data, s_type, speaker='', target=''):
        event = data['event']

        # if event == 'tech':
        #     # 기술 멘트
        #     audio_files =   list(range(158,161))
            
        # elif event == 'cheer':
        #     # 격려
        #     audio_files =   list(range(161,162))

        # elif event == 'humor':
        #     # 유머
        #     audio_files =   list(range(163,164))

        if event == 'random':
            audio_files = list(filter(lambda af: af['category1'] == 'RD' and af['type'] == s_type and af['speaker'] == speaker, self.audio_files))

        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            if audio_file['file_name'] != self.prev_file:
                print(audio_file['file_name'],self.prev_file)
                self.playFile(audio_file['file_name'])
                self.prev_file = audio_file['file_name']

    def lapDistance(self, data, s_type, speaker='', target=''):
        event = data['event']
        print(s_type, speaker, target)
        audio_files = []
        if event == 'start':
            # 시작
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'ST' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
            
        elif event == 'tunnel':
            # 터널
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'T' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        elif event == 'deep_curve':
            # 급한커브
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'C3' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'curve':
            # 커브
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and (af['category2'] == 'C1' or af['category2'] == 'C2') and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'straight':
            # 직선
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'SR' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'finish':
            # 종료
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'E' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'section_1':
            # 1구간
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'T1' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'section_2':
            # 2구간
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'T2' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'section_3':
            # 3구간
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'T3' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))

        elif event == 'r_finish':
            # 종료 후
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'FIN' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        print(audio_files)
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            if audio_file['file_name'] != self.prev_file:
                print(audio_file['file_name'],self.prev_file)
                self.playFile(audio_file['file_name'])
                self.prev_file = audio_file['file_name']

    def speed_check(self, data, s_type, speaker='', target=''):
        status = data['status']

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'MI' and af['category2'] == 'SL' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            if audio_file['file_name'] != self.prev_file:
                self.playFile(audio_file['file_name'])
                self.prev_file = audio_file['file_name']

    def finish(self, data, s_type, speaker='', target=''):
        rank = data['rank']

        if rank == 1:
            audio_files = list(filter(lambda af: af['category1'] == 'RS' and af['category2'] == 'WIN' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        else:
            audio_files = list(filter(lambda af: af['category1'] == 'RS' and af['category2'] == 'LOSE' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def before_start(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'RS' and af['category2'] == 'BS' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def finish_furby(self, data, s_type, speaker='', target=''):
        rank = data['rank']

        if rank == 1:
            audio_files = list(filter(lambda af: af['category1'] == 'RS' and af['category2'] == 'WIN' and af['type'] == s_type and af['target'] == 'P1' and af['speaker'] == speaker, self.audio_files))
        else:
            audio_files = list(filter(lambda af: af['category1'] == 'RS' and af['category2'] == 'WIN' and af['type'] == s_type and af['target'] == 'P2' and af['speaker'] == speaker, self.audio_files))
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def intro(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'RE' and af['category2'] == 'INT' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def ready_1(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'RE' and af['category2'] == 'R1' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def ready_2(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'RE' and af['category2'] == 'R2' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def game_start(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'RE' and af['category2'] == 'GS' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])

    def problem(self, data, s_type, speaker='', target=''):
        status = data

        if status:
            audio_files = list(filter(lambda af: af['category1'] == 'PB' and af['category2'] == 'PB' and af['type'] == s_type and af['target'] == target and af['speaker'] == speaker, self.audio_files))
        
        if len(audio_files) > 0:
            audio_file = random.choice(audio_files)
            self.playFile(audio_file['file_name'])