import subprocess 
import multiprocessing as mp
from threading import Thread
from multiprocessing import Pool
from queue import Empty

import time
import datetime
import os
import signal

import sqlite3

import redis

class overtakeChecker(mp.Process):

    def __init__(self,que,r,target_ip):
        # [공통] 기본설정
        super(overtakeChecker,self).__init__()
        self.event = mp.Event()
        self.queue = que
        self.r = r
        self.target_ip = target_ip

        self.channels = self.r.pubsub()
        self.channels.subscribe(self.target_ip)

        # Variables
        self.r0_t0 = 0
        self.c = False
        self.status = False

        
    def get_rank(self, data):
        ranks = [info['mRacePosition'] for info in data["participants"]["mParticipantInfo"]]
        return ranks

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

        

    def run(self):
        while True:
            # time.sleep(0.1)

            message = self.r.hget(self.target_ip,'msg')
            # self.r.hdel(self.target_ip,'msg')
            if message:
                data = eval(message)

                gamedata = data['gamedata']
                current_time = data['current_time']

                # Codes
                if "participants" in gamedata:
                    sim_index = self.get_sim_name(self.target_ip,gamedata)
                    lap_length = gamedata["eventInformation"]["mTrackLength"] # 랩 길이
                    lap_completed = gamedata["participants"]["mParticipantInfo"][sim_index]["mLapsCompleted"]
                    
                    lap_distance = gamedata["participants"]["mParticipantInfo"][sim_index]["mCurrentLapDistance"] + lap_length * lap_completed

                    if lap_distance > 10:
                        ranks = self.get_rank(gamedata)

                        if len(ranks) > 1:
                            r0_t1 = ranks[sim_index]
                            
                            if self.r0_t0 != 0:
                                
                                if self.r0_t0 > r0_t1:
                                    # Overtaked
                                    print(self.target_ip,'추월')
                                    self.c = ranks.index(r0_t1 + 1)
                                    self.status = True
                                elif self.r0_t0 < r0_t1:
                                    # Overtaken
                                    print(self.target_ip,'추월당함')
                                    self.c = ranks.index(r0_t1 - 1)
                                    self.status = False
                                else:
                                    self.c = False

                            if self.c:
                                c_name = gamedata["participants"]["mParticipantInfo"][self.c]["mName"]
                                current_time = str(datetime.datetime.now())

                                result = {}
                                result['current_time'] = current_time
                                result['target_ip'] = self.target_ip
                                result['flag'] = 'overtake'
                                result['data'] = {
                                    'status': self.status,
                                    'rank': r0_t1
                                }

                                self.r.hdel(self.target_ip,'msg')
                                self.r.hset(self.target_ip, 'results', result)

                            self.r0_t0 = r0_t1

    def stop(self):
        self.event.set()
        self.join()
            