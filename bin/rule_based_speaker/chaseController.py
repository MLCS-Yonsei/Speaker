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

import sqlite3

class chaseChecker(mp.Process):

    def __init__(self,que,r,target_ip):
        # [공통] 기본설정
        super(chaseChecker,self).__init__()
        self.queue = que
        self.r = r
        self.target_ip = target_ip

        self.channels = self.r.pubsub()
        self.channels.subscribe(self.target_ip)

        # Variables
        self.recent_fcar_distances = []
        self.recent_scar_distances = []

        self.msg_rate = 0.02
        
    def get_sim_name(self, target_ip, gamedata):
        participants = gamedata['participants']['mParticipantInfo']

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

        

    
    def get_distance(self, data):
        ranks = [info['mRacePosition'] for info in data["participants"]["mParticipantInfo"]]
        # lap을 distance에 포함시키면 됨
        lap_length = data["eventInformation"]["mTrackLength"] # 랩 길이
        ecar_current_lap = data["participants"]["mParticipantInfo"][0]["mLapsCompleted"]
        ecar_distance = data["participants"]["mParticipantInfo"][0]["mCurrentLapDistance"]

        sim_index = self.get_sim_name(self.target_ip,data)

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


    def run(self):
        while True:
            time.sleep(0.3)
            message = self.r.hget(self.target_ip,'msg')
            # self.r.hdel(self.target_ip,'msg')
            if message:
                data = eval(message)

                gamedata = data['gamedata']
                current_time = data['current_time']
                
                racestate= gamedata["gameStates"]["mRaceState"]
                    
                # Codes
                if "participants" in gamedata:

                    sim_index = self.get_sim_name(self.target_ip,gamedata)
                    lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
                    lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
                    
                    lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed
                    
                    if racestate != 2:
                        self.recent_fcar_distances = []
                        self.recent_scar_distances = []
                    elif lap_distance < 10:
                        self.recent_fcar_distances = []
                        self.recent_scar_distances = []
                    else:

                        rank, ecar_distance, fcar_distance, scar_distance, ranks = self.get_distance(gamedata)
                        '''
                        fcar_distance랑 ecar_distance랑 차이 해서 특정만큼 벌어지면 그때
                        기다려줘요 멘트 ㄱ
                        혹은 독주상황이라 볼 수 있음.
                        '''
                        if ecar_distance > 200:
                            
                            # 앞차 쫓는 상황
                            if ranks[self.get_sim_name(self.target_ip,gamedata)] != min(ranks):
                                if len(self.recent_fcar_distances) == 20:
                                    self.recent_fcar_distances = self.recent_fcar_distances[1:]
                                    self.recent_fcar_distances.append(fcar_distance)

                                    if random.random() < self.msg_rate:
                                        
                                        current_time = str(datetime.datetime.now())

                                        result = {}
                                        result['current_time'] = current_time      
                                        result['target_ip'] = self.target_ip
                                        result['flag'] = 'chase'
                                        
                                        result['data'] = {
                                            'chasing': True,
                                            'rank': rank,
                                            'acc': '',
                                            'alone': False
                                        }  

                                        if self.recent_fcar_distances[19] - self.recent_fcar_distances[0] < 100 and self.recent_fcar_distances[19] < 50:
                                            # 잘 쫓아가고 있을때
                                            print(self.target_ip,'잘 쫒아감!')
                                            result['data']['acc'] = True
                                        elif self.recent_fcar_distances[19] - self.recent_fcar_distances[0] > 100 and self.recent_fcar_distances[19] < 50:
                                            # 잘 쫓아가지 못할때
                                            print(self.target_ip,'잘 못쫒아감!')
                                            result['data']['acc'] = False

                                        if result['data']['acc'] != '':
                                            self.r.hdel(self.target_ip,'msg')
                                            self.r.hset(self.target_ip, 'results', result)
                                    
                                elif len(self.recent_fcar_distances) < 20:
                                    self.recent_fcar_distances.append(fcar_distance)
                            else: 
                                self.recent_fcar_distances = []

                            self.recent_scar_distances.append(ecar_distance - scar_distance)

                            # 뒷차에게 쫓기는 상황
                            if ranks[self.get_sim_name(self.target_ip,gamedata)] != max(ranks):
                                if len(self.recent_scar_distances) == 20:
                                    self.recent_scar_distances = self.recent_scar_distances[1:]
                                    self.recent_scar_distances.append(fcar_distance)

                                    if random.random() < self.msg_rate:

                                        current_time = str(datetime.datetime.now())

                                        result = {}
                                        result['current_time'] = current_time      
                                        result['target_ip'] = self.target_ip
                                        result['flag'] = 'chase'
                                        
                                        result['data'] = {
                                            'chasing': False,
                                            'rank': rank,
                                            'alone': False
                                        }  

                                        if self.recent_scar_distances[19] - self.recent_scar_distances[0] > 100 and self.recent_scar_distances[19] < 50:
                                            # 잘 도망가고 있을때
                                            print(self.target_ip,'잘 도망가!')
                                            result['data']['acc'] = True
                                        elif  self.recent_scar_distances[19] - self.recent_scar_distances[0] < 100 and self.recent_scar_distances[19] < 50:
                                            # 따라잡히고 있을때
                                            print(self.target_ip,'쫓아와!')
                                            result['data']['acc'] = False

                                        if result['data']['acc'] != '':
                                            self.r.hdel(self.target_ip,'msg')
                                            self.r.hset(self.target_ip, 'results', result)
                                    
                                elif len(self.recent_scar_distances) < 20:
                                    self.recent_scar_distances.append(fcar_distance)
                            else: 
                                self.recent_scar_distances = []
