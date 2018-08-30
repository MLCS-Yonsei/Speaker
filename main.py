# send_crest_request
from utils import *
# from detection import Cam, detect_hand, detect_human, detect_gender
from audioPlayer import audioPlayer

import time
import random
from threading import Thread

import requests 

from bin.rule_based_speaker.rules import lap_distance, overtake, crash, chase

import multiprocessing as mp

target_ips = ['ubuntu.hwanmoo.kr:8080']
dev = True
audio_overlap = True
enable_broadcasting = False

def init_var():
    return {
        'person_attr': None,
        'intro': False,
        'playing': False,
        'outro': False,
        'lap_distance_t': 0,
        'overtake_r0_t0': None,
        'prev_crash': None,
        'recent_fcar_distances': [],
        'recent_scar_distances': [],
        'audio_thread': None
    }

def launch_cam(var, target_ip):
    if target_ip == 'ubuntu.hwanmoo.kr:8080':
        var['cam_id'] = 1
        # var['cam'] = Cam(variables[target_ip]['cam_id'], dev)

    return var

def launch_audio(var, target_ip):
    var['audio_player'] = audioPlayer(target_ip)

    return var


variables = {}
for target_ip in target_ips:
    variables[target_ip] = init_var()

local_audio_player = audioPlayer('localhost')
for target_ip in target_ips:
    variables[target_ip] = launch_cam(variables[target_ip], target_ip)
    variables[target_ip] = launch_audio(variables[target_ip], target_ip)

while True:
    for target_ip in target_ips:
        stage, gamedata = get_crest_data(target_ip)
        # print("Stage:", stage)
        # stage = 1
        _v = variables[target_ip]
        # print("#2")
        if stage == 1 and _v['playing'] == False:
            '''
            로비에서 대기중인 상황.
            crop_detector로 모니터링하다가 사람이 탑승하면 age/gender/color 파악하고 정보 저장.
            파악이 끝나면 기본 안내멘트 재생.
            재생 후 양손이 디텍트되면 게임 스타트 매크로 시작. + 스타트 멘트 재생
            '''
            cam = _v['cam']
            # print(_v['person_attr'])
            if _v['person_attr'] == None:
                while True:
                    human_box = detect_human(cam)
                    gender = detect_gender(human_box)

                    if gender is not False:
                        break

                # print("G:",gender)
                _v['person_attr'] = {
                    'gender': gender
                }

                print("#1")
            else:
                if _v['intro'] == False:
                    a_thread = Thread(target = playFile, args = (target_ip,'test_intro', ))
                    a_thread.start()

                    print("Playing intro file, sleep for ", 27, "Seconds")
            
                    a_thread.join()

                    _v['intro'] = True

                if _v['intro'] == True and _v['playing'] == False:
                    hand_detection = detect_hand(cam)
                    print("#3", hand_detection)

                    if detection_result == 1:
                        time.sleep(0.5)
                        a_thread = Thread(target = playFile, args = (target_ip,'test_gamestart', ))
                        a_thread.start()

                        _v['playing'] = True

                        url = 'http://' + target_ip.split(':')[0] + ':3000/start'
                        r = requests.get(url)

                        a_thread.join()

        elif stage == 2:
            '''
            로딩중 별다른 액션 없음.
            '''
            pass
        elif stage == 3:
            '''
            게임중 Speaker 시작
            '''
            # with mp.Pool(processes=4) as pool:

            #     lap_distance = pool.apply_async(lap_distance, (gamedata, target_ip, _v['lap_distance_t']))
            #     overtake = pool.apply_async(overtake, (gamedata, target_ip, _v['overtake_r0_t0']))
            #     crash = pool.apply_async(crash, (gamedata, target_ip, _v['prev_crash'], 1))
            #     chase = pool.apply_async(chase, (gamedata, target_ip, _v['recent_fcar_distances'], _v['recent_scar_distances'], 0.02))

            #     (lap_distance_result, _v['lap_distance_t']) = lap_distance.get()
            #     overtake_result, _v['overtake_r0_t0'] = overtake.get()
            #     crash_result, _v['prev_crash'] = crash.get()
            #     chase_result, _v['recent_fcar_distances'], _v['recent_scar_distances'] = chase.get()

            #     pool.close()
            #     pool.join()

            lap_distance_result, _v['lap_distance_t'] = lap_distance(gamedata, target_ip, _v['lap_distance_t'])
            overtake_result, _v['overtake_r0_t0'] = overtake(gamedata, target_ip, _v['overtake_r0_t0'])
            crash_result, _v['prev_crash'] = crash(gamedata, target_ip, _v['prev_crash'], 1)
            chase_result, _v['recent_fcar_distances'], _v['recent_scar_distances'] = chase(gamedata, target_ip, _v['recent_fcar_distances'], _v['recent_scar_distances'], 0.02)

            # 중계를 할지 내비를 할지 선택
            if enable_broadcasting is True:
                s_type = random.choice(['NV', 'BR'])
            elif enable_broadcasting is False:
                s_type = 'BR'

            if s_type == 'NV':
                audio_player = _v['audio_player']
                target = ''
            elif s_type == 'BR':
                audio_player = local_audio_player
                # 여기에서 플레이어 비교
                target = 'P1'
            
            rb_data = None
            if lap_distance_result is not False:
                rb_data = lap_distance_result
            elif overtake_result is not False:
                rb_data = overtake_result
            elif crash_result is not False:
                rb_data = crash_result
            elif chase_result is not False:
                rb_data = chase_result

            if rb_data is not None and audio_overlap is False:
                # 오디오 중첩 없이 재생
                audio_player.play(rb_data, s_type, target)
            elif rb_data is not None and audio_overlap is True:
                # 오디오 중첩 재생
                if _v['audio_thread'] is None:
                    # print("Playing audio")
                    _v['audio_thread'] = Thread(target=audio_player.play, args=(rb_data, s_type, target))
                    _v['audio_thread'].start()
                    # print(_v['audio_thread'].isAlive())

                if not _v['audio_thread'].isAlive():
                    # print("Still Playing audio")
                    _v['audio_thread'] = None

            # print(lap_distance_result, overtake_result, crash_result, chase_result, target_ip)

        elif stage == 4:
            '''
            완주
            종료 멘트 재생, stage 1로 대기
            '''
            if _v['outro'] is False:
                _v = init_var()

                a_thread = Thread(target = playFile, args = (target_ip,'test_outro', ))
                a_thread.start()

                print("Playing intro file, sleep for ", 5, "Seconds")
                
                a_thread.join()

                _v['outro'] = True

            _v['intro'] = False
            _v['playing'] = False
        elif stage == 5:
            '''
            나가기
            종료 멘트 재생, stage 1로 대기
            '''
            if _v['outro'] is False:
                _v = init_var()

                a_thread = Thread(target = playFile, args = (target_ip,'test_outro', ))
                a_thread.start()

                print("Playing intro file, sleep for ", 5, "Seconds")
                
                a_thread.join()

                _v['outro'] = True

            _v['intro'] = False
            _v['playing'] = False
        else:
            pass
