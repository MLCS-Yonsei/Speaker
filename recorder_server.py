from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import time
import os


sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('', 9000))
sock.listen(1)

client_sock, addr = sock.accept()

start = time.time()
now = time.localtime()
timestamp = "%04d%02d%02d%02d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
filename = timestamp + '.txt'
f = open(filename, 'w')
f.write("start time: {}\n".format(timestamp))
f.close()


def convert_time(current_time):
    t = int(current_time - start)
    hour = int(t / 3600)
    r = t % 3600
    minute = int(r / 60)
    seconds = r % 60

    return "%02d:%02d:%02d" % (hour, minute, seconds)


def record(msg):
    label = msg.split(":")[1]
    t = convert_time(time.time())
    print("label:",label)
    while True:
        try:
            file = open(filename, 'a')
            file.write("{} {}\n".format(t, label))
            file.close()
            print("file saved")
            break

        except:
            continue


while True:
    recv = client_sock.recv(32)
    if not recv:
        continue

    msg = recv.decode('utf-8')
    thread = Thread(target=record, args=(msg,))
    thread.start()





