import random
import sqlite3
import datetime
from datetime import datetime
import requests 
from threading import Thread
from utils import *
import numpy as np
from PIL import ImageGrab
import time
from socket import socket, AF_INET, SOCK_STREAM


distance_offset = -100  # minus -> delay nav capture
remote_screenshot = True


if remote_screenshot:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('192.168.0.31', 9000))

    print("Connected to Screenshot Server")


def screenshot_thread(label, now, count):

    timestamp = "%04d%02d%02d%02d%02d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, count)
    filename = "screenshots/{}/{}.png".format(label, label + timestamp)
    img = ImageGrab.grab()
    img.save(filename)
    print("Screenshot saved: {}".format(filename))


def screenshot(label):

    if remote_screenshot:
        sock.send(label.encode('utf-8'))
    else:
        start = time.time()
        count = 0
        now = time.localtime()

        while time.time() - start < 5:
            count += 1
            thread = Thread(target=screenshot_thread, args=(label, now, count))
            thread.start()


def get_images():
    sock.send('done'.encode('utf-8'))
    msg = sock.recv(32)

    while True:
        if msg.decode('utf-8') == 'bb':
            break

        if msg.decode('utf-8') == 'aa':  # 이미지 한 장 들어옴
            filename = sock.recv(1000).decode('utf-8')
            filesize = int(sock.recv(1000).decode('utf-8'))

            img = open(filename, 'wb')

            while filesize > 0:
                data = sock.recv(100000)
                img.write(data)

                filesize -= 100000

            img.close()




def check_reset_timing(data, d, t, target_ip, car_position_reset_time):
    gamedata = data['gamedata']

    sim_index = get_sim_name(target_ip,gamedata)
    lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
    lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
    lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed
    if t is None:
        t = datetime.datetime.now()

    if lap_distance > 10:
        if int(d) == int(lap_distance):
            cur_t = datetime.datetime.now()

            delta = cur_t - t
            if delta.seconds > car_position_reset_time:
                # 리셋
                print("Reset the car")
                # a_thread = Thread(target = playFile, args = (target_ip,'test_reset_car', ))
                # a_thread.start()

                # url = 'http://' + target_ip.split(':')[0] + ':3000/car_position_reset'
                # r = requests.get(url)

                # a_thread.join()

                t = None
        else:
            t = datetime.datetime.now()

    return lap_distance, t

def lap_distance(data, target_ip, t):
    # msg_rate = 0.003
    msg_rate = 1

    gamedata = data['gamedata']
    current_time = data['current_time']

    # Codes
    # current_time = str(datetime.datetime.now())

    result = {}
    result['current_time'] = current_time      
    result['target_ip'] = target_ip
    result['flag'] = 'lapDistance'

    sim_index = get_sim_name(target_ip,gamedata)
    lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
    lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
    lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed
    racestate= gamedata["gameStates"]["mRaceState"]

    result['data'] = {
        'lapDistance' : lap_distance,
        'event' : ''
    }
    
    if racestate == 2:

        lap_distance = lap_distance + distance_offset
        if t == 0 and racestate == 2 and lap_distance < 100:
            print(target_ip,'start')
            t += 1
            result['data']['event'] = 'start'

        elif 90 < lap_distance < 95 :
            # print('터널입니다')
            result['data']['event'] = 'tunnel'
            screenshot('tunnel')

        elif 790 < lap_distance < 810 :
            # print('앞에 급한 커브입니다')
            result['data']['event'] = 'deep_curve'
            screenshot('curve_deep')
        
        elif 1240 < lap_distance < 1260 :
            # print('앞에 급한 커브입니다')
            result['data']['event'] = 'deep_curve'
            screenshot('curve_deep')

        elif 1440 < lap_distance < 1460 :
            # 1/4 지점
            result['data']['event'] = 'section_1'

        elif 1890 < lap_distance < 1910 :
            # print('앞에 완만한 s자 커브입니다')
            result['data']['event'] = 'curve'
            screenshot('curve_mild_s')

        elif 2490 < lap_distance < 2510 :
            # print('앞에 완만한 s자 커브입니다')
            result['data']['event'] = 'curve'
            screenshot('curve_mild_s')

        elif 2890 < lap_distance < 2810 :
            # 1/2 지점
            result['data']['event'] = 'section_2'

        elif 3290 < lap_distance < 3300 :
            # print('이제부터 직선 구간입니다')
            result['data']['event'] = 'straight'
            screenshot('straight')

        elif 4320 < lap_distance < 4330 :
            # 3/4 지점
            result['data']['event'] = 'section_3'

        elif 4800 < lap_distance < 4820 :
            # print('거의 다 왔습니다')
            result['data']['event'] = 'finish'
            
        elif lap_completed < 4900:
            if random.random() < msg_rate:
                result['flag'] = 'random'
                # random_events = [
                #     'tech', 
                #     'cheer', 
                #     'humor'
                # ]
                # result['data']['event'] = random.choice(random_events)
                result['data']['event'] = 'random'
            
            else:
                result = False
        '''
        + 이 외 lap_distance 일 때 random 하게 trigger하고, random한 pool에서 뽑하서 말하기
        + 전체 랩길이 -> 데이터에 있음 -> 1/4 , 1/2, 3/4 지점 90% 지점
        section_1
        section_2
        section_3

        '''

        if racestate == 3 and t == 0:
            t = 0
            print('끝났습니다')
            if 'data' in result:
                result['data']['event'] = 'r_finish'

        if lap_distance > 100:
            t = 0

    if result and result['data']['event'] == '':
        result = False

    return result, t

def get_rank(data):
    ranks = [info['mRacePosition'] for info in data["participants"]["mParticipantInfo"]]
    return ranks

def get_sim_name(target_ip, gamedata):
    participants = gamedata['participants']['mParticipantInfo']
    # print(participants)
    # DB for config
    conn = sqlite3.connect("./config/db/test.db")
    cur = conn.cursor()

    # Getting Simulator info
    cur.execute("select * from simulators")
    _sims = cur.fetchall()
    
    # Connection 닫기
    conn.close()

    target_name = False

    for sim in _sims:
        if sim[0] == target_ip:
            target_name = sim[1]
    if target_name:
        for i, p in enumerate(participants):
            if p['mName'] == target_name:
                return i

    return False
    
def overtake(data, target_ip, r0_t0):
    gamedata = data['gamedata']
    current_time = data['current_time']
    
    c = False
    status = False

    result = False

    # Codes
    if "participants" in gamedata:
        sim_index = get_sim_name(target_ip,gamedata)
        lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
        lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
        
        lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed

        if lap_distance > 10:
            ranks = get_rank(gamedata)

            if len(ranks) > 1:
                r0_t1 = ranks[sim_index]
                
                if r0_t0 != 0 and r0_t0 is not None:
                    
                    if r0_t0 > r0_t1:
                        # Overtaked
                        print(target_ip,'추월')
                        screenshot('overtake')

                        try:
                            c = ranks.index(r0_t1 + 1)
                            status = True
                        except:
                            pass
                    elif r0_t0 < r0_t1:
                        # Overtaken
                        print(target_ip,'추월당함')
                        screenshot('overtaken')

                        try:
                            c = ranks.index(r0_t1 - 1)
                            status = False
                        except:
                            pass
                    else:
                        c = False

                if c:
                    c_name = gamedata["participants"]["mParticipantInfo"][c]["mName"]
                    
                    result = {}
                    result['current_time'] = current_time
                    result['target_ip'] = target_ip
                    result['flag'] = 'overtake'
                    result['data'] = {
                        'status': status,
                        'rank': r0_t1,
                        'op_name': c_name
                    }

                r0_t0 = r0_t1
                
    return result, r0_t0


def crash(data, target_ip, prev_crash, msg_rate):
    gamedata = data['gamedata']
    current_time = data['current_time']
    
    racestate= gamedata["gameStates"]["mRaceState"]

    result = False
    
    if racestate == 2:
        # Codes
        '''
        지금 도로를 이탈하였는지 확인하고, (terrein 부분 제거?)
        전체 velocity가 특정 값으로 내려오면 행동불능 상태로 판명
        
        아니면 그냥
        crash state 발생했을때
        그 레벨 (1,2,3)에 대해 강도 멘트. 2는 거의 없고 1 : 가벼운 충돌, 3 : 강력한 충돌 위주로.

        mworldpoisition -> 변화량 측정해서 lap_distance의 변화량의 어느 정도 보다 적으면 후진이나 차빼기 멘트
        '''

        if 'carDamage' in gamedata:
            crash_state = int(gamedata['carDamage']['mCrashState'])

            if random.random() < msg_rate:
                if crash_state > 0:
                    if prev_crash != crash_state:
                        if crash_state == 1:
                            print(target_ip, "lv.1 충돌 발생")

                        elif crash_state == 2:
                            print(target_ip, "lv.2 충돌 발생")

                        elif crash_state == 3:
                            print(target_ip, "lv.3 충돌 발생")

                        result = {}
                        result['current_time'] = current_time      
                        result['target_ip'] = target_ip
                        result['flag'] = 'collision'
                        result['data'] = {
                            'crash_state' : crash_state,
                            'moving' : True,
                        }

                        prev_crash = crash_state

    return result, prev_crash

def get_distance(data, target_ip):
    ranks = [info['mRacePosition'] for info in data["participants"]["mParticipantInfo"]]
    # lap을 distance에 포함시키면 됨
    lap_length = data["eventInformation"]["mTrackLength"] # 랩 길이
    ecar_current_lap = data["participants"]["mParticipantInfo"][0]["mLapsCompleted"]
    ecar_distance = data["participants"]["mParticipantInfo"][0]["mCurrentLapDistance"]

    sim_index = get_sim_name(target_ip,data)

    if sim_index is not None:
        if ranks[sim_index] != min(ranks):
            fcar_current_lap = data["participants"]["mParticipantInfo"][ranks.index(ranks[sim_index]-1)]["mLapsCompleted"]
            fcar_distance = data["participants"]["mParticipantInfo"][ranks.index(ranks[sim_index]-1)]["mCurrentLapDistance"] - ecar_distance + lap_length * fcar_current_lap
        else:
            fcar_distance = ecar_distance
        
        if ranks[sim_index] != max(ranks):
            scar_current_lap = data["participants"]["mParticipantInfo"][ranks.index(ranks[sim_index]+1)]["mLapsCompleted"]
            scar_distance = ecar_distance - data["participants"]["mParticipantInfo"][ranks.index(ranks[sim_index]+1)]["mCurrentLapDistance"] + lap_length * scar_current_lap
        else:
            scar_distance = ecar_distance


        return ranks[sim_index], ecar_distance, fcar_distance, scar_distance, ranks
    else:
        return False
        
def chase(data, target_ip, recent_fcar_distances, recent_scar_distances, msg_rate):
    gamedata = data['gamedata']
    current_time = data['current_time']
    
    racestate= gamedata["gameStates"]["mRaceState"]
        
    result = False
    # Codes
    if "participants" in gamedata:

        sim_index = get_sim_name(target_ip,gamedata)
        lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
        lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
        
        lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed
        
        if racestate != 2:
            recent_fcar_distances = []
            recent_scar_distances = []
        elif lap_distance < 10:
            recent_fcar_distances = []
            recent_scar_distances = []
        else:
            try:
                rank, ecar_distance, fcar_distance, scar_distance, ranks = get_distance(gamedata, target_ip)
            except:
                return None, recent_fcar_distances, recent_scar_distances
            '''
            fcar_distance랑 ecar_distance랑 차이 해서 특정만큼 벌어지면 그때
            기다려줘요 멘트 ㄱ
            혹은 독주상황이라 볼 수 있음.
            '''
            if ecar_distance > 200:
                
                # 앞차 쫓는 상황
                if ranks[get_sim_name(target_ip,gamedata)] != min(ranks):
                    if len(recent_fcar_distances) == 20:
                        recent_fcar_distances = recent_fcar_distances[1:]
                        recent_fcar_distances.append(fcar_distance)

                        if random.random() < msg_rate:
                            
                            current_time = str(datetime.datetime.now())

                            result = {}
                            result['current_time'] = current_time      
                            result['target_ip'] = target_ip
                            result['flag'] = 'chase'
                            
                            result['data'] = {
                                'chasing': True,
                                'rank': rank,
                                'acc': '',
                                'alone': False
                            }  

                            if 0 < recent_fcar_distances[0] - recent_fcar_distances[19] < 80 and 30 < recent_fcar_distances[19] < 50:
                                # 잘 쫓아가고 있을때
                                print(target_ip,'잘 쫒아감!')
                                result['data']['acc'] = True
                                screenshot('chasing')

                            elif recent_fcar_distances[19] - recent_fcar_distances[0] > 100 and recent_fcar_distances[19] < 50:
                                # 잘 쫓아가지 못할때
                                print(target_ip,'잘 못쫒아감!')
                                result['data']['acc'] = False
                                screenshot('cheerup')

                            if result['data']['acc'] != '':
                                return result, recent_fcar_distances, recent_scar_distances
                        
                    elif len(recent_fcar_distances) < 20:
                        recent_fcar_distances.append(fcar_distance)
                else: 
                    recent_fcar_distances = []

                recent_scar_distances.append(ecar_distance - scar_distance)

                # 뒷차에게 쫓기는 상황
                if ranks[get_sim_name(target_ip,gamedata)] != max(ranks):
                    if len(recent_scar_distances) == 20:
                        recent_scar_distances = recent_scar_distances[1:]
                        recent_scar_distances.append(fcar_distance)

                        if random.random() < msg_rate:

                            current_time = str(datetime.datetime.now())

                            result = {}
                            result['current_time'] = current_time      
                            result['target_ip'] = target_ip
                            result['flag'] = 'chase'
                            
                            result['data'] = {
                                'chasing': False,
                                'rank': rank,
                                'alone': False
                            }

                            if recent_scar_distances[19] - recent_scar_distances[0] > 100 and 50 < recent_scar_distances[19]:
                                # 잘 도망가고 있을때
                                print(target_ip,'잘 도망가!')
                                result['data']['acc'] = True
                            elif 0 < recent_scar_distances[0] - recent_scar_distances[19] < 80 and recent_scar_distances[19] < 50:
                                # 따라잡히고 있을때
                                print(target_ip,'쫓아와!')
                                result['data']['acc'] = False

                            if result['data']['acc'] != '':
                                return result, recent_fcar_distances, recent_scar_distances
                        
                    elif len(recent_scar_distances) < 20:
                        recent_scar_distances.append(fcar_distance)
                else: 
                    recent_scar_distances = []

    return result, recent_fcar_distances, recent_scar_distances

def speed_check(data, target_ip, fp_dist, fp_sp):
    gamedata = data['gamedata']
    current_time = data['current_time']
    status = False
    speed = gamedata["carState"]["mSpeed"]
    distance = gamedata["participants"]["mParticipantInfo"][0]["mCurrentLapDistance"]

    result = {}
    result['current_time'] = current_time      
    result['target_ip'] = target_ip
    result['flag'] = 'speed_check'

    if  800 < distance < 820 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    elif  965 < distance < 985 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    elif  1370 < distance < 1390 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    elif  1485 < distance < 1505 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    elif  2760 < distance < 2780 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    elif  2850 < distance < 2870 and speed > np.interp(distance, fp_dist, fp_sp):
        status = True
        result['data'] = {
            'status' : status
        }

    else:
        result = False

    return result

