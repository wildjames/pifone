import fnmatch
import os
import random
import threading
import time
import wave
import numpy as np

import pyaudio

try:
    import gpiozero

except: pass

AUDIO_FILES_LOCATION = "/home/pi/pifone"

class Listener():
    # Playback, file reading, polling settings
    CHUNK = 1024
    POLLING_RATE = 0.01 #s
    play = False
    record = False
    _playing = False
    _recording = False

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100


    def __init__(self):
        # try:
            # This is the old version of the pinout. I've since moved on to a proper dialler
            # pin17 = gpiozero.DigitalInputDevice(pin=17)
            # pin27 = gpiozero.DigitalInputDevice(pin=27)
            # pin22 = gpiozero.DigitalOutputDevice(pin=22, initial_value=True)
            # print("Successfully initialised cradle to pins 17, 27, 22")

            # pin5   = gpiozero.DigitalInputDevice(pin=5)
            # pin6   = gpiozero.DigitalInputDevice(pin=6)
            # pin13  = gpiozero.DigitalOutputDevice(pin=13, initial_value=True)
            # print("Successfully initialised cradle to pins 5, 6, 13")

        self.cradle_pin  = gpiozero.DigitalInputDevice(pin=27)
        print("Initialised the cradle input")

        self.grpA_pin = gpiozero.DigitalOutputDevice(pin=5, initial_value=False)
        self.grpB_pin = gpiozero.DigitalOutputDevice(pin=6, initial_value=False)
        self.grpC_pin = gpiozero.DigitalOutputDevice(pin=7, initial_value=False)
        self.grpD_pin = gpiozero.DigitalOutputDevice(pin=8, initial_value=False)
        print("Initialised Output pins")

        self.outA_pin = gpiozero.DigitalInputDevice(pin=9)
        self.outB_pin = gpiozero.DigitalInputDevice(pin=10)
        self.outC_pin = gpiozero.DigitalInputDevice(pin=11)
        self.outD_pin = gpiozero.DigitalInputDevice(pin=12)
        self.inpins = [self.outA_pin, self.outB_pin, self.outC_pin, self.outD_pin]
        print("Initialised Input pins")


        self.rpi = True
        # except:
        #     self.rpi = False
        #     print("Not running on a raspberry pi!")

        os.chdir(AUDIO_FILES_LOCATION)
        self.button_functions = []
        print("OK, GO")
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        if self.rpi:
            # self.play = self.pin27.value
            # self.record = self.pin6.value
            self.play = self.cradle_pin.value

            button_pressed = np.nan
            # Check the first button group
            self.grpA_pin.value = True
            outputs = ['redial', '#', 0, '*']
            for i, pin in enumerate(self.inpins):
                if pin.value:
                    button_pressed = outputs[i]
                    break
            self.grpA_pin.value = False

            # Check the second group
            self.grpB_pin.value = True
            outputs = [np.nan, 9, 8, 7]
            for i, pin in enumerate(self.inpins):
                if pin.value:
                    button_pressed = outputs[i]
                    break
            self.grpB_pin.value = False

            # Check the Third group
            self.grpC_pin.value = True
            outputs = [np.nan, 6, 5, 4]
            for i, pin in enumerate(self.inpins):
                if pin.value:
                    button_pressed = outputs[i]
                    break
            self.grpC_pin.value = False

            # Check the fourth group
            self.grpD_pin.value = True
            outputs = [np.nan, 3, 2, 1]
            for i, pin in enumerate(self.inpins):
                if pin.value:
                    button_pressed = outputs[i]
                    break
            self.grpD_pin.value = False

        print("Pushed the button {}".format(button_pressed))
        # if button_pressed != np.nan:
        #     function = self.button_functions[button_pressed]
        #     self.buttonthread = threading.Thread(target=function).start()

        # If we're not playing, then we shouldn't be recording or playing.
        if self.play == False:
            self._playing = False
            self._recording = False
            try:
                self.buttonthread.join()
            except: pass

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
            frames_per_buffer=self.CHUNK,
            output_device_index=self.device_ID,
        )
        print("Recording...")
        frames = []

        try:
            while self.play:
                data = stream.read(self.CHUNK)
                frames.append(data)
        except Exception as e:
            print("Crashed during recording")
            print(e)

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

        try:
            #play stream
            if listen:
                while data and self.play and self._playing:
                    #print("Write stream")
                    stream.write(data)
                    #print('Read data')
                    data = f.readframes(self.CHUNK)
            else:
                while data:
                    stream.write(data)
                    data = f.readframes(self.CHUNK)
        except Exception as e:
            print("Crashed during recording")
            print(e)

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
        for root, dirnames, filenames in os.walk("AUDIO_FILES"):
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
