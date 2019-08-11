import fnmatch
import os
import random
import threading
import time
import wave

import pyaudio

try:
    import gpiozero
except: pass

AUDIO_FILES_LOCATION = "/home/pi/pifone"

class Listener():
    # Playback, file reading, polling settings
    CHUNK = 1024
    POLLING_RATE = 0.5 #s
    play = False
    record = False
    _playing = False
    _recording = False

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    try:
        pin17 = gpiozero.DigitalInputDevice(pin=17)
        pin27 = gpiozero.DigitalInputDevice(pin=27)
        pin22 = gpiozero.DigitalOutputDevice(pin=22, initial_value=True)
        print("Successfully initialised cradle to pins 17, 27, 22")

        pin5   = gpiozero.DigitalInputDevice(pin=5)
        pin6   = gpiozero.DigitalInputDevice(pin=6)
        pin13  = gpiozero.DigitalOutputDevice(pin=13, initial_value=True)
        print("Successfully initialised cradle to pins 5, 6, 13")
        rpi = True
    except:
        rpi = False
        print("Not running on a raspberry pi!")

    def __init__(self):
        os.chdir(AUDIO_FILES_LOCATION)
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        # os.system("clear")
        # print("\n\nCurrent values:")
        # print("Active threads: {}".format(threading.activeCount()))
        # print("Play Switch:          {}".format(self.play))
        # print("Record Switch:        {}".format(self.record))
        # print("Currently playing?    {}".format(self._playing))
        # print("Currently recording?  {}".format(self._recording))
        if self.rpi:
            # print("pin17:   {}".format(self.pin17.value))
            # print("pin27:   {}".format(self.pin27.value))
            # print("pin22:   {}".format(self.pin22.value))

            # print("pin5:    {}".format(self.pin5.value))
            # print("pin6:    {}".format(self.pin6.value))
            # print("pin13:   {}".format(self.pin13.value))

            self.play = self.pin27.value
            self.record = self.pin6.value


        # If we're not playing, then we shouldn't be recording or playing.
        if self.play == False:
            self._playing = False
            self._recording = False

        if self._recording == False:
            # print("I'm not recording! Do I need to start any threads?")
            # Start a play thread
            if self._playing == False:
                if self.play == True:
                    print("Starting a random playback thread")
                    threading.Thread(target=self.play_random).start()

            # start a record thread
            if self.play:
                if self.record:
                    print("Starting a recording thread")
                    threading.Thread(target=self.make_recording).start()

        # time.sleep(self.POLLING_RATE)
        # self._listen()
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def make_recording(self):
        # Setting self.play = False stops the existing sound
        self._playing = False
        self._recording = True
        print("Set self._recording to TRUE")

        # Wait two ticks to ensure the playback is stopped
        time.sleep(self.POLLING_RATE*2)

        # Get the name of the new audio file to create
        audio_files = [0]
        for root, dirnames, filenames in os.walk("AUDIO_FILES/RECORDED/"):
            for filename in fnmatch.filter(filenames, "*.wav"):
                fname = filename.lower().replace('.wav', '')
                try:
                    audio_files.append(int(fname))
                except: pass

        new_file = "{:05d}.wav".format(max(audio_files) + 1)
        new_file = os.path.join("AUDIO_FILES", "RECORDED", new_file)
        print("Making a new file: {}".format(new_file))

        self.play_clip("AUDIO_FILES/RECORDED/Intro.wav")

        # Init the audio handler
        p = pyaudio.PyAudio()

        # Start recording, until the cradle is activated
        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        print("Recording...")
        frames = []

        while self.play:
            data = stream.read(self.CHUNK)
            frames.append(data)

        print("Done recording...")

        # Close my stuff
        stream.stop_stream()
        stream.close()

        # Reconstruct the wav, for saving
        waveFile = wave.open(new_file, 'wb')
        waveFile.setnchannels(self.CHANNELS)
        waveFile.setsampwidth(p.get_sample_size(self.FORMAT))
        waveFile.setframerate(self.RATE)

        waveFile.writeframes(b''.join(frames))
        waveFile.close()

        p.terminate()

        self._playing = False
        self.play_clip("AUDIO_FILES/RECORDED/Thanks.wav", False)

        # No longer busy
        self._recording = False
        print("Finished saving recording to {}".format(new_file))

    def play_clip(self, playme, listen=True):
        if self._playing:
            return

        print("Starting a new playback, file {}".format(playme))

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True

        f = wave.open(playme, 'rb')
        p = pyaudio.PyAudio()

        stream = p.open(
            format=p.get_format_from_width(f.getsampwidth()),
            channels=f.getnchannels(),
            rate=f.getframerate(),
            output=True
        )

        # read data
        data = f.readframes(self.CHUNK)

        #play stream
        if listen:
            while data and self.play and self._playing:
                print("Wrote stream")
                stream.write(data)
                print('Read data')
                data = f.readframes(self.CHUNK)
        else:
            while data:
                stream.write(data)
                data = f.readframes(self.CHUNK)

        print("Done with playback!")

        #stop stream
        stream.stop_stream()
        stream.close()
        f.close()

        #close PyAudio
        p.terminate()

        # I'm no longer playing.
        self._playing = False
        print("Finished playback")

    def get_audio_files(self):
        audio_files = []
        for root, dirnames, filenames in os.walk("AUDIO_FILES/DICTAPHONE_DIARIES"):
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


    time.sleep(2)

    print("!!!!! PRESSING PLAY SWITCH")
    l.play = True

    time.sleep(3)

    print("!!!!! PRESSING RECORDING SWITCH")
    l.record = True

    time.sleep(2)

    print("!!!!! RELEASING RECORDING SWITCH")
    l.record = False

    time.sleep(12)

    print("!!!!! RELEASING PLAY SWITCH")
    l.play = False

    time.sleep(13)

    print("!!!! DONE")

    exit()

#     l.play_random()
