# send_crest_request
from utils import *
from detection import Cam, detect_hand, detect_human, detect_gender
from audioPlayer import audioPlayer
import numpy as np
import time
import random
from threading import Thread

import requests 

from bin.rule_based_speaker.rules import lap_distance, overtake, crash, chase, check_reset_timing, speed_check

import multiprocessing as mp
import pyudev

target_ips = [
    # 'ubuntu.hwanmoo.kr:8080',
    '192.168.0.2:9090'
]
dev = True
audio_overlap = True
enable_broadcasting = False
oposite_gender_speaker = True
enable_half_voice = False
car_position_reset_time = 5

speed_label = np.load('output.npz')['data']
fp_dist = speed_label[:,0].astype(float)
fp_sp = speed_label[:,1].astype(float)
# fp_steer = speed_label[:,2].astype(float)

def init_var():
    return {
        'person_attr': {
            'gender': None
        },
        'intro': False,
        'playing': False,
        'outro': False,
        'lap_distance_t': 0,
        'overtake_r0_t0': None,
        'prev_crash': None,
        'recent_fcar_distances': [],
        'recent_scar_distances': [],
        'audio_thread': None,
        'lap_distance': 0,
        'lap_distance_time': None
    }

def reset_game_var(var):
    var['outro'] = False
    var['lap_distance_t'] = 0
    var['overtake_r0_t0'] = None
    var['prev_crash'] = None
    var['recent_fcar_distances'] = []
    var['recent_scar_distances'] = []
    var['lap_distance'] = 0
    var['lap_distance_time'] = None

    return var

def reset_var(var):
    var['intro'] = False
    var['playing'] = False
    var['person_attr']['gender'] = None

    return var

# def launch_cam(var, target_ip):
#     if target_ip == '192.168.0.2:9090':
#         var['cam_id'] = 0
#         var['cam'] = Cam(variables[target_ip]['cam_id'], dev)
#     if target_ip == '192.168.0.52:9090':
#         var['cam_id'] = 1
#         var['cam'] = Cam(variables[target_ip]['cam_id'], dev)

#     return var

def launch_cam(var, target_ip):
    context = pyudev.Context()

    for device in context.list_devices(subsystem='usb'):
        if device.get('DEVPATH') == '/devices/pci0000:00/0000:00:14.0/usb1/1-7/1-7.4':
            #192.168.0.2
            ip02 = int(device.get('DEVNUM'))
        
        elif device.get('DEVPATH') == '/devices/pci0000:00/0000:00:14.0/usb1/1-8/1-8.4':
            #192.168.0.52
            ip52 = int(device.get('DEVNUM'))

    if ip02 < ip52:
        if target_ip == '192.168.0.2:9090':
            var['cam_id'] = 0
            var['cam'] = Cam(variables[target_ip]['cam_id'], dev)
        if target_ip == '192.168.0.52:9090':
            var['cam_id'] = 1
            var['cam'] = Cam(variables[target_ip]['cam_id'], dev)
        
    else:
        if target_ip == '192.168.0.2:9090':
            var['cam_id'] = 1
            var['cam'] = Cam(variables[target_ip]['cam_id'], dev)
        if target_ip == '192.168.0.52:9090':
            var['cam_id'] = 0
            var['cam'] = Cam(variables[target_ip]['cam_id'], dev)

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
        try:
            stage, gamedata = get_crest_data(target_ip)
        except:
            continue
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
            # print(_v)
            if 'cam' in _v:
                cam = _v['cam']
                # print(_v)
                if _v['person_attr']['gender'] == None:
                    while True:
                        human_box = detect_human(cam)
                        gender = detect_gender(human_box)
                        print("13")
                        if gender is not False:
                            break

                    # print("G:",gender)
                    _v['person_attr']['gender'] = gender

                    print("#1")
                else:
                    if _v['intro'] == False:
                        a_thread = Thread(target = playFile, args = (target_ip,'test_intro', ))
                        print("Playing intro file, sleep for ", 27, "Seconds")
                        a_thread.start()
                        a_thread.join()

                        _v['intro'] = True

                    if _v['intro'] == True and _v['playing'] == False:
                        hand_detection = detect_hand(cam)
                        print("#3", hand_detection)

                        if hand_detection == 1:
                            time.sleep(0.5)
                            a_thread = Thread(target = playFile, args = (target_ip,'test_gamestart', ))
                            a_thread.start()

                            _v['playing'] = True

                            url = 'http://' + target_ip.split(':')[0] + ':3000/host_ready'
                            r = requests.get(url)
                            
                            url = 'http://' + target_ip.split(':')[0] + ':3000/host_start'
                            r = requests.get(url)
                                    
                            a_thread.join()

        elif stage == 2:
            '''
            로딩중 별다른 액션 없음.
            '''
            _v = reset_game_var(_v)
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
            _v['lap_distance'], _v['lap_distance_time'] = check_reset_timing(gamedata, _v['lap_distance'], _v['lap_distance_time'], target_ip, car_position_reset_time)

            lap_distance_result, _v['lap_distance_t'] = lap_distance(gamedata, target_ip, _v['lap_distance_t'])
            overtake_result, _v['overtake_r0_t0'] = overtake(gamedata, target_ip, _v['overtake_r0_t0'])
            crash_result, _v['prev_crash'] = crash(gamedata, target_ip, _v['prev_crash'], 1)
            chase_result, _v['recent_fcar_distances'], _v['recent_scar_distances'] = chase(gamedata, target_ip, _v['recent_fcar_distances'], _v['recent_scar_distances'], 0.01)
            speed_check_result = speed_check(gamedata, target_ip, fp_dist, fp_sp)

            # 중계를 할지 내비를 할지 선택
            if enable_broadcasting is True:
                s_type = random.choice(['NV', 'BR'])
            elif enable_broadcasting is False:
                if enable_half_voice is True:
                    s_type = 'HFNV'
                else:
                    s_type = 'NV'

            if s_type == 'NV':
                audio_player = _v['audio_player']
                target = ''

                speaker_gender = _v['person_attr']['gender']

                if oposite_gender_speaker == True:
                    if speaker_gender == 'M':
                        speaker_gender = 'F'
                    else:
                        speaker_gender = 'M'
            elif s_type == 'BR':
                audio_player = local_audio_player
                # 여기에서 플레이어 비교
                target = 'P1'
                speaker_gender = _v['person_attr']['gender']

                if oposite_gender_speaker == True:
                    if speaker_gender == 'M':
                        speaker_gender = 'F'
                    else:
                        speaker_gender = 'M'
            elif s_type == 'HFNV':
                audio_player = _v['audio_player']
                target = ''

                speaker_gender = 'F'
        
            rb_data = None
            if overtake_result is not False:
                rb_data = overtake_result
            elif lap_distance_result is not False and lap_distance_result['flag'] is not 'random':
                rb_data = lap_distance_result
            elif speed_check_result is not False:
                rb_data = speed_check_result
            elif crash_result is not False:
                rb_data = crash_result
            elif chase_result is not False:
                rb_data = chase_result
            elif lap_distance_result is not False and lap_distance_result['flag'] is 'random':
                rb_data = lap_distance_result

            if rb_data is not None and audio_overlap is False:
                # 오디오 중첩 없이 재생
                audio_player.play(rb_data, s_type, speaker_gender, target)
            elif rb_data is not None and audio_overlap is True:
                # 오디오 중첩 재생
                if _v['audio_thread'] is None:
                    # print("Playing audio")
                    _v['audio_thread'] = Thread(target=audio_player.play, args=(rb_data, s_type, speaker_gender, target))
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
            crest_data = send_crest_requset(target_ip, "crest-monitor", {})
            rank = crest_data["participants"]["mParticipantInfo"][0]["mRacePosition"]
            result = {}
            result['target_ip'] = target_ip
            result['flag'] = 'finish'
            result['data'] = {
            'rank' : rank
            }
            audio_player.play(result, s_type, speaker_gender, target)

            if _v['outro'] is False:
                if audio_overlap is False:
                    a_thread = Thread(target = playFile, args = (target_ip,'test_outro', ))
                    a_thread.start()

                    print("#1 Playing outro file, sleep for ", 5, "Seconds", target_ip)
                    
                    a_thread.join()

                    _v['outro'] = True
                elif audio_overlap is True:
                    # 오디오 중첩 재생
                    if _v['audio_thread'] is None:
                        # print("Playing audio")
                        _v['audio_thread'] = Thread(target = playFile, args = (target_ip,'test_outro', ))
                        _v['audio_thread'].start()
                        # print(_v['audio_thread'].isAlive())

                    if not _v['audio_thread'].isAlive():
                        # print("Still Playing audio")
                        _v['audio_thread'] = None
                        _v['outro'] = True

            _v = reset_var(_v)
            time.sleep(5)
            url = 'http://' + target_ip.split(':')[0] + ':3000/finish'
            r = requests.get(url)
            time.sleep(10)

        elif stage == 5:
            '''
            나가기
            종료 멘트 재생, stage 1로 대기
            '''
            crest_data = send_crest_requset(target_ip, "crest-monitor", {})
            rank = crest_data["participants"]["mParticipantInfo"][0]["mRacePosition"]
            result = {}
            result['target_ip'] = target_ip
            result['flag'] = 'finish'
            result['data'] = {
            'rank' : rank
            }
            audio_player.play(result, s_type, speaker_gender, target)

            if _v['outro'] is False:
                if audio_overlap is False:
                    a_thread = Thread(target = playFile, args = (target_ip,'test_outro', ))
                    a_thread.start()

                    print("#1 Playing outro file, sleep for ", 5, "Seconds", target_ip)
                    
                    a_thread.join()

                    _v['outro'] = True
                elif audio_overlap is True:
                    # 오디오 중첩 재생
                    if _v['audio_thread'] is None:
                        # print("Playing audio")
                        _v['audio_thread'] = Thread(target = playFile, args = (target_ip,'test_outro', ))
                        _v['audio_thread'].start()
                        # print(_v['audio_thread'].isAlive())

                    if not _v['audio_thread'].isAlive():
                        # print("Still Playing audio")
                        _v['audio_thread'] = None
                        _v['outro'] = True

            _v = reset_var(_v)
            time.sleep(5)
            url = 'http://' + target_ip.split(':')[0] + ':3000/finish'
            r = requests.get(url)
            time.sleep(10)

        else:
            pass

        variables[target_ip] = _v
