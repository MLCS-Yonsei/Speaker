from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import os
from math import log, ceil, floor
import time
import wave
import random
import struct
import numpy as np

dir = '/Users/jehyun/code/Speaker/bin/audio/'
filenames = os.listdir(dir)
file_path = os.path.join(dir,filenames[50])

seg = AudioSegment.from_wav('before_start_short.wav')
# seg = AudioSegment.from_wav('1-8.wav')
p = pyaudio.PyAudio()
Rate = 1
audio_format = pyaudio.paInt16
stream = p.open(format=audio_format,
                channels=seg.channels,
                rate=int(seg.frame_rate * Rate),
                output=True)
def make_chunks(audio_segment, chunk_length):
    """
    Breaks an AudioSegment into chunks that are <chunk_length> milliseconds
    long.
    if chunk_length is 50 then you'll get a list of 50 millisecond long audio
    segments back (except the last one, which can be shorter)
    """
    number_of_chunks = ceil(len(audio_segment) / float(chunk_length))
    return [audio_segment[i * chunk_length:(i + 1) * chunk_length] for i in range(int(number_of_chunks))]

# break audio into half-second chunks (to allows keyboard interrupts)
# st = time.time()
frames = []
for i, chunk in enumerate(make_chunks(seg, 17)):
    if i % 10 != 0:
        stream.write(chunk._data)
        frames.append(chunk._data)
# ft = time.time()

stream.stop_stream()
stream.close()
p.terminate()

# waveFile = wave.open('1.2.wav', 'wb')
# waveFile.setnchannels(seg.channels)
# waveFile.setsampwidth(p.get_sample_size(audio_format))
# waveFile.setframerate(int(seg.frame_rate * Rate))
# waveFile.writeframes(b''.join(frames))
# waveFile.close()

