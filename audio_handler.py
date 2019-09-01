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
    POLLING_RATE = 0.1 #s
    play = False
    record = False
    _playing = False
    _recording = False

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100


    def __init__(self):
        self.cradle_pin  = gpiozero.DigitalInputDevice(pin=22)
        print("Initialised the cradle input")

        self.grpA_pin = gpiozero.DigitalOutputDevice(pin=12, initial_value=False)
        self.grpB_pin = gpiozero.DigitalOutputDevice(pin=11, initial_value=False)
        self.grpC_pin = gpiozero.DigitalOutputDevice(pin=10, initial_value=False)
        self.grpD_pin = gpiozero.DigitalOutputDevice(pin=9, initial_value=False)
        print("Initialised Output pins")

        self.outA_pin = gpiozero.DigitalInputDevice(pin=8)
        self.outB_pin = gpiozero.DigitalInputDevice(pin=7)
        self.outC_pin = gpiozero.DigitalInputDevice(pin=6)
        self.outD_pin = gpiozero.DigitalInputDevice(pin=5)
        self.inpins = [self.outA_pin, self.outB_pin, self.outC_pin, self.outD_pin]
        print("Initialised Input pins")

        self.button_functions = {
            'redial': self.start_recording,
            '*': self.not_implimented,
            '#': self.not_implimented,
            0:   self.not_implimented,
            1:   self.not_implimented,
            2:   self.not_implimented,
            3:   self.not_implimented,
            4:   self.not_implimented,
            5:   self.not_implimented,
            6:   self.not_implimented,
            7:   self.not_implimented,
            8:   self.not_implimented,
            9:   self.not_implimented,
        }

        os.chdir(AUDIO_FILES_LOCATION)
        print("OK, GO")
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        # If the cradle is raised, play is True
        self.play = not self.cradle_pin.value

        ##################################################################
        ########## Check if any of the buttons have been pushed ##########
        ##################################################################
        button_pressed = None

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

        if not button_pressed is None:
            print("Pushed the button {}".format(button_pressed))
            function = self.button_functions[button_pressed]

            # Start the button's function
            self.buttonthread = threading.Thread(target=function).start()


        ##################################################################
        ################# Cradle raised: start playback. #################
        ##################################################################

        # If we're not playing, then we shouldn't be recording or playing.
        if self.play == False:
            self._playing = False
            self._recording = False

        # If we aren't recording, then we should check to see if we just
        # lifted the handset
        if self._recording == False:
            # Start a play thread only if we aren't already playing
            if self._playing == False:
                if self.play == True:
                    print("Handset raised")
                    threading.Thread(target=self.play_random).start()

            # start a record thread, if we already lifted the handset and pushed the button
            if self.play:
                if self.record:
                    print("Starting a recording thread")
                    threading.Thread(target=self.make_recording).start()

        threading.Timer(self.POLLING_RATE, self._listen).start()

    def not_implimented(self):
        # make this flash an LED or something, just to show the user something was noticed?
        print("Button does nothing :(")

    def start_recording(self):
        print("#####################################################")
        print("Starting a recording")
        print("#####################################################")
        self.record = True

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
        self.stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            # output_device_index=self.device_ID,
        )
        print("Recording...")
        frames = []

        try:
            while self.play:
                data = self.stream.read(self.CHUNK)
                frames.append(data)
        except Exception as e:
            print("Crashed during recording")
            print(e)

        print("Done recording...")

        # Close my stuff
        self.stream.stop_stream()
        self.stream.close()

        if frames != []:
            # Reconstruct the wav, for saving
            waveFile = wave.open(new_file, 'wb')
            waveFile.setnchannels(self.CHANNELS)
            waveFile.setsampwidth(p.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)

            waveFile.writeframes(b''.join(frames))
            waveFile.close()

        p.terminate()

        # No longer busy
        self._playing = False
        self._recording = False
        print("Finished saving recording to {}".format(new_file))

    def play_clip(self, playme):
        if self._playing:
            print("Already playing")
            return

        print("Starting a new playback, file {}".format(playme))

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True

        f = wave.open(playme, 'rb')
        p = pyaudio.PyAudio()

        self.stream = p.open(
            format=p.get_format_from_width(f.getsampwidth()),
            channels=f.getnchannels(),
            rate=f.getframerate(),
            output=True
        )

        # read data
        data = f.readframes(self.CHUNK)

        try:
            while data:
                self.stream.write(data)
                data = f.readframes(self.CHUNK)
        except Exception as e:
            print("Crashed during recording")
            print(e)

        print("Done with playback!")

        #stop self.stream
        self.stream.stop_stream()
        self.stream.close()
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
