from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from PIL import ImageGrab
import time
import os


sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('', 9000))
sock.listen(1)

client_sock, addr = sock.accept()

screenshots = []



def send_images():
    global screenshots

    for img in screenshots:
        # 'aa', 파일이름, 파일사이즈 순서로 보냄
        client_sock.sendall('aa'.encode('utf-8'))
        time.sleep(0.01)
        client_sock.sendall(img.encode('utf-8'))
        time.sleep(0.01)

        filesize = str(os.path.getsize(img))
        client_sock.sendall(filesize.encode('utf-8'))
        time.sleep(0.01)

        f = open(img, 'rb')
        line = f.read(100000)
        while line:
            client_sock.sendall(line)
            line = f.read(100000)

        f.close()

    client_sock.sendall('bb'.encode('utf-8'))

    screenshots = []



def screenshot_thread(label, now, count):

    timestamp = "%04d%02d%02d%02d%02d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, count)
    filename = "screenshots/{}/{}.png".format(label, label + timestamp)
    img = ImageGrab.grab()
    img.save(filename)
    screenshots.append(filename)
    print("Screenshot saved: {}".format(filename))


def screenshot(label):

    start = time.time()
    count = 0
    now = time.localtime()
    while time.time() - start < 5:
        count += 1
        thread = Thread(target=screenshot_thread, args=(label, now, count))
        thread.start()


while True:
    recv = client_sock.recv(32)
    if not recv:
        continue

    msg = recv.decode('utf-8')

    if msg == 'done':
        send_images()
    else:
        screenshot(msg)















