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
    DEBUG = True
    CHUNK = 1024
    POLLING_RATE = 0.5 #s
    play = False
    _playing = False

    try:
        green  = gpiozero.DigitalInputDevice(pin=17)
        black = gpiozero.DigitalInputDevice(pin=27)
        red = gpiozero.DigitalOutputDevice(pin=22, initial_value=True)
        print("Successfully initialised to pins 17, 27, 22")
        rpi = True
    except:
        rpi = False
        print("Not running on a raspberry pi!")

    def __init__(self):
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        # os.system("clear")
        if self.DEBUG:
            print("Current values:")
            print("Currently playing?  {}".format(self._playing))
            print("play: {}".format(self.play))
            if self.rpi:
                print("Green:   {}".format(self.green.value))
                print("Black:   {}".format(self.black.value))
                print("Red:     {}".format(self.red.value))

        if self.rpi:
            self.play = bool(self.black.value)

        if self.play is False:
            self._playing = False

        # If we weren't playing, but now are, start a playback thread
        if self._playing == False and self.play == True:
            threading.Thread(target=self.play_random).start()

        # Call the next poll
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def play_clip(self, playme):
        if self._playing:
            return

        if self.DEBUG:
            print("Starting a new playback")

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True

        try:
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
                print("Reading data")
                stream.write(data)
                data = f.readframes(self.CHUNK)
                print("Data: {}\n\n\n")
            print("Stopped reading data!\n\n")

            #stop stream
            stream.stop_stream()
            stream.close()
            f.close()

            #close PyAudio
            p.terminate()
        except Exception as e:
            print("I fucked up!")
            print(e)

        # I'm no longer playing.
        self._playing = False

        if self.DEBUG:
            print("Finished playback")

    def get_audio_files(self):
        audio_files = []
        for root, dirnames, filenames in os.walk("AUDIO_FILES/"):
            for filename in fnmatch.filter(filenames, "*.wav"):
                fname = os.path.join(root, filename)
                audio_files.append(fname)

        if self.DEBUG:
            print("I found {} audio files:".format(len(audio_files)))
            for fn in audio_files:
                print("- {}".format(fn))

        self.audio_files = audio_files


    def play_random(self):
        if self._playing:
            return

        self.get_audio_files()

        playme = random.choice(self.audio_files)
        if self.DEBUG:
            print("Playing file:\n{}\n".format(playme))

        self.play_clip(playme)


if __name__ in "__main__":
    l = Listener()

#     l.play_random()