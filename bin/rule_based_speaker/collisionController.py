import subprocess 
import multiprocessing as mp
from threading import Thread
from multiprocessing import Pool
from queue import Empty

import time
import datetime
import os
import signal

import redis
import random
class collisionChecker(mp.Process):

    def __init__(self,que,r,target_ip):
        # [공통] 기본설정
        super(collisionChecker,self).__init__()
        self.queue = que
        self.r = r
        self.target_ip = target_ip

        self.channels = self.r.pubsub()
        self.channels.subscribe(self.target_ip)

        # Variables
        self.acc_lap_distances = []
        self.msg_rate = 1
        self.prev_crash = 0

    def run(self):
        while True:
            message = self.r.hget(self.target_ip,'msg')
            # try:
            if message:
                data = eval(message)

                gamedata = data['gamedata']
                current_time = data['current_time']
                
                racestate= gamedata["gameStates"]["mRaceState"]
                if racestate == 2:
                    # Codes
                    current_time = str(datetime.datetime.now())
                    
                    result = {}
                    result['current_time'] = current_time      
                    result['target_ip'] = self.target_ip
                    result['flag'] = 'collision'
                    

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

                        if random.random() < self.msg_rate:
                            if crash_state > 0:
                                if self.prev_crash != crash_state:
                                    if crash_state == 1:
                                        print(self.target_ip, "lv.1 충돌 발생")

                                    elif crash_state == 2:
                                        print(self.target_ip, "lv.2 충돌 발생")

                                    elif crash_state == 3:
                                        print(self.target_ip, "lv.3 충돌 발생")

                                    result['data'] = {
                                        'crash_state' : crash_state,
                                        'moving' : True,
                                        
                                    }
                                    self.r.hdel(self.target_ip,'msg')
                                    self.r.hset(self.target_ip, 'results', result)

                                    self.prev_crash = crash_state
                    time.sleep(0.4)
                    '''
                    # 이동없음 상태 판별
                    if 'motionAndDeviceRelated' in gamedata and 'eventInformation' in gamedata and 'participants' in gamedata:
                        lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
                        lap_completed = gamedata["participants"]["mParticipantInfo"][0]["mLapsCompleted"]
                        lap_distance = gamedata["participants"]["mParticipantInfo"][0]["mCurrentLapDistance"] + lap_length * lap_completed
                        
                        if len(self.acc_lap_distances) == 40:
                            self.acc_lap_distances = self.acc_lap_distances[1:]
                            self.acc_lap_distances.append(lap_distance)

                            velocity = sum( i*i for i in gamedata["motionAndDeviceRelated"]["mLocalVelocity"])

                            if self.acc_lap_distances[19] - self.acc_lap_distances[0] < 3 and self.acc_lap_distances[19] < 10:
                                # 출발 안함
                                result['data'] = {
                                    'crash_state' : crash_state,
                                    'moving' : False
                                }
                            elif self.acc_lap_distances[19] - self.acc_lap_distances[0] < 3 and self.acc_lap_distances[19] > 60:
                                # 출발 안함
                                result['data'] = {
                                    'crash_state' : crash_state,
                                    'moving' : False
                                }
                            if 'data' in result:
                                if result['data']['moving'] == False:
                                    self.r.hdel(self.target_ip,'msg')
                                    self.r.hset(self.target_ip, 'results', result)

                        elif len(self.acc_lap_distances) < 40:
                                self.acc_lap_distances.append(lap_distance)
                            
                        # collision = gamedata["wheelsAndTyres"]["mTerrain"][0] != 0 and gamedata["wheelsAndTyres"]["mTerrain"][2] !=0
                        # velocity = sum( i*i for i in gamedata["motionAndDeviceRelated"]["mLocalVelocity"])

                        # if collision and velocity < 1.5 :
                        #     print('collision')
                        #     result['data'] = {
                        #     'collision' : True
                        # }
                        '''
                    
            # except Exception as e:
            #     print(e)
            #     print('Failed in collision checker')

            # time.sleep(0.1)
                
                