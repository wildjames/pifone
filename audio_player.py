import fnmatch
import os
import random

import pyaudio
import wave

import threading
try:
    import gpiozero
except: pass



class Listener():
    CHUNK = 1024
    play = True

    try:
        C  = gpiozero.DigitalInputDevice(pin=0)
        NO = gpiozero.DigitalInputDevice(pin=2)
        NC = gpiozero.DigitalInputDevice(pin=3)
    except:
        print("Not running on a raspberry pi!")

    def __init__(self):
        threading.Timer(3, self._listen).start()

    def _listen(self):
        print("Current values:")
        print("play: {}".format(self.play))
        if hasattr(self, "C"):
            print("C:   {}".format(self.C.value))
            print("NC:  {}".format(self.NC.value))
            print("NO:  {}".format(self.NO.value))

        threading.Timer(3, self._listen).start()

    def stop(self):
        self.play = False

    def play_clip(self, playme):
        f = wave.open(playme, 'rb')
        p = pyaudio.PyAudio()

        stream = p.open(
            format = p.get_format_from_width(f.getsampwidth()),
            channels = f.getnchannels(),
            rate = f.getframerate(),
            output = True
        )

        # read data
        data = f.readframes(self.CHUNK)

        #play stream
        while data and self.play:
            stream.write(data)
            data = f.readframes(self.CHUNK)

        #stop stream
        stream.stop_stream()
        stream.close()
        f.close()

        #close PyAudio
        p.terminate()

    def get_audio_files(self):
        audio_files = []
        for root, dirnames, filenames in os.walk("AUDIO_FILES/"):
            for filename in fnmatch.filter(filenames, "*.wav"):
                fname = os.path.join(root, filename)
                audio_files.append(fname)

        print("I found {} audio files:".format(len(audio_files)))
        for fn in audio_files:
            print("- {}".format(fn))

        self.audio_files = audio_files


    def play_random(self):
        self.get_audio_files()

        playme = random.choice(self.audio_files)
        print("Playing file:\n{}\n".format(playme))

        self.play_clip(playme)


if __name__ in "__main__":
    l = Listener()

    l.play_random()