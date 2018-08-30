import sys
sys.path.insert(0, '../routes')

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

from overtakeController import overtakeChecker
from chaseController import chaseChecker
from lapDistanceController import lapDistanceChecker
from collisionController import collisionChecker

class controller():

    def __init__(self):
        self.jobs = []
        self.queues = []

    def checkOvertake(self, r, target_ip):
        q = mp.Queue()
        job = overtakeChecker(q,r,target_ip)
        self.queues.append(q)
        self.jobs.append(job)
        job.start()

        return job

    def chaseChecker(self, r, target_ip):
        q = mp.Queue()
        job = chaseChecker(q,r,target_ip)
        self.queues.append(q)
        self.jobs.append(job)
        job.start()

        return job

    def lapDistanceChecker(self, r, target_ip):
        q = mp.Queue()
        job = lapDistanceChecker(q,r,target_ip)
        self.queues.append(q)
        self.jobs.append(job)
        job.start()

        return job

    def collisionChecker(self, r, target_ip):
        q = mp.Queue()
        job = collisionChecker(q,r,target_ip)
        self.queues.append(q)
        self.jobs.append(job)
        job.start()

        return job