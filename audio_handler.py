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
    POLLING_RATE = .1 #s
    play = False
    _playing = False

    try:
        green  = gpiozero.DigitalOutputDevice(pin=17, initial_value=True)
        black = gpiozero.DigitalInputDevice(pin=27)
        red = gpiozero.DigitalInputDevice(pin=22)
        print("Successfully initialised to pins 17, 27, 22")
        rpi = True
    except:
        rpi = False
        print("Not running on a raspberry pi!")

    def __init__(self):
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        # os.system("clear")
        print("Current values:")
        print("Currently playing?  {}".format(self._playing))
        print("play: {}".format(self.play))
        if self.rpi:
            print("Green:   {}".format(self.green.value))
            print("Black:   {}".format(self.black.value))
            print("Red:     {}".format(self.red.value))

            self.play = self.black.value

        if self._playing == False and self.play == True:
            threading.Thread(target=self.play_random).start()

        threading.Timer(self.POLLING_RATE, self._listen).start()

    def play_clip(self, playme):
        if self._playing:
            return

        print("Starting a new playback")

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True

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

        # I'm no longer playing.
        self._playing = False
        print("Finished playback")

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

#     l.play_random()