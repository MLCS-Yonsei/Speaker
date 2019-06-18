import http.client
import csv 
import json
import os.path
import time
import datetime

from pydub import AudioSegment
import requests

def crop_img(img,box):
    y,x,d = img.shape
    startx = int(x*box[0])
    starty = int(y*box[1])
    endx = int(x*box[3])
    endy = int(y*box[2])

    return img[starty:endy,startx:endx]
    
def playFile(target_ip, file_path):
    print("Playing...",file_path)
    file_path = str(file_path) + '.wav'
    # sound = AudioSegment.from_wav('./bin/audio/' + file_path)
    url = 'http://' + target_ip.split(':')[0] + ':3000/play?path=/bin/audio/' + file_path
    r = requests.get(url)

    print("Play Request Finished.")
    return True

def send_crest_requset(url, flag, option):
    url = 'http://' + url + '/crest/v1/api'
    # try:
        
    # except Exception as e:
    #     print("CREST_ERROR on send_crest_request:", e)

    #     return False


    r = requests.get(url, timeout=0.4)

    data = json.loads(r.text)

    return data

def get_crest_data(target_ip):
    # 데이터 가져오기
    # print("crest get call")
    crest_data = send_crest_requset(target_ip, "crest-monitor", {})

    try:
        gameStates = crest_data['gameStates']

        gameState = gameStates['mGameState']
        sessionState = gameStates['mSessionState']
        raceState = gameStates['mRaceState']

        # print("gameState:",gameState,"/ sessionState:",sessionState,"/ raceState:",raceState, "/ Current IP :", target_ip)

        if gameState == 1 and raceState == 0:
            # Stage 1 : 로비 + 로딩 일부
            return 1, None
        
        elif gameState == 1 and raceState == 1:
            # Stage 2 : 로딩 중
            return 2, None

        elif gameState == 2 and raceState == 1:
            # Stage 2 : 로딩 마무리 중
            return 2, None

        elif gameState == 2 and raceState == 2:
            # Stage 3 : 게임중
            if 'participants' in crest_data:
                current_time = str(datetime.datetime.now())
                gamedata = {'current_time': current_time, 'gamedata': crest_data}
                print("Game Data",gamedata)
            else:
                gamedata = None

            return 3, gamedata

        elif gameState == 2 and raceState == 3:
            # Stage 4 : 완주
            return 4, None

        elif gameState == 3:
            # Stage 5 : 나가기
            return 5, None

    except Exception as e:
        print("Crest Error on get_crest_data:",e)
        return False, None