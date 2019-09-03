import fnmatch
import os
import random
import sys
import threading
import time
import wave
from pathlib import Path
import requests

import numpy as np
import pyaudio
import wave

import threading
try:
    import gpiozero

except: pass

AUDIO_FILES_LOCATION = "/home/pi/pifone"


class Listener():
    NUMVERIFY_APIKEY = "55d54bda772465a9979d9c78ca1b7313"

    CHUNK = 1024
    POLLING_RATE = 0.05 #s

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    FORBIDDEN_AUDIO = [
        'Intro',
        'Thanks',
        'VOYAGER',
        'CUM',
    ]

    def __init__(self, start=False):
        '''Set up the pin I/O.

        If start is True, also start the polling thread.'''
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
            None:     self.not_implimented,
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

        self.konami = [5, 5, '*', '*', 8, 2, 8, 2, '#', '*', 'redial']
        self.kill_seq = [4, 2, 8, 6]
        self.cummy = [2, 1, 0, 8]
        self.voyager = [1, 9, 7, 7]

        self._playing = False
        self._recording = False
        self._interrupt = False

        self._handset_was_up = False
        self._handset_is_up  = False

        self._is_polling = False
        self._call_func  = False
        self.button_seq  = []
        self._call_seq   = True
        self.last_button = None
        self.last_button_pressed_at = time.time()

        os.chdir(AUDIO_FILES_LOCATION)
        print("Initialised successfully!")

        if start:
            self.start()

    def interrupt_playback(self):
        '''Stops current playback without having to replace the handset'''
        self._interrupt = True
        print("INTERRUPTING PLAYBACK")

    def start(self):
        '''Start the polling function.'''
        self._is_polling = True
        print("OK, GO")

        threading.Timer(self.POLLING_RATE, self.parse_button).start()
        threading.Timer(self.POLLING_RATE, self.poll_buttons).start()

    def stop(self):
        '''Stop polling'''
        self._is_polling = False
        self._handset_is_up = False

    def quit(self):
        self.stop()
        self.interrupt_playback()
        time.sleep(self.POLLING_RATE*10)
        exit()

    def poll_buttons(self):
        '''Check what button was last pushed'''
        self._interrupt = False
        # If the cradle is raised, play is True
        self._handset_is_up = not self.cradle_pin.value
        if not self._handset_is_up and self._handset_was_up:
            print("Handset in cradle")
            self._handset_was_up = False
            self.interrupt_playback()

        if not self._handset_is_up:
            self.button_seq = []
            self._call_seq = True
            self._playing = False
            self._interrupt = True

        if not self._handset_was_up and self._handset_is_up:
            self.handset_lifted()

        ############################################################
        # # # # Check if any of the buttons have been pushed # # # #
        ############################################################
        button_pressed = None

        # Check the first button group
        self.grpA_pin.value = True
        outputs = ['redial', '#', 0, '*']
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpA_pin.value = False

        # Check the second group
        self.grpB_pin.value = True
        outputs = [np.nan, 9, 8, 7]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpB_pin.value = False

        # Check the Third group
        self.grpC_pin.value = True
        outputs = [np.nan, 6, 5, 4]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpC_pin.value = False

        # Check the fourth group
        self.grpD_pin.value = True
        outputs = [np.nan, 3, 2, 1]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpD_pin.value = False

        # If a button was pushed, say so
        if button_pressed is not None:
            if self.last_button is None:
                self.button_seq.append(button_pressed)
                # Raise a flag to call this button's function, if it has one
                self._call_func = True

        self.last_button = button_pressed
        self.last_button_pressed_at = time.time()

        if self._is_polling:
            threading.Timer(self.POLLING_RATE, self.poll_buttons).start()

    def parse_button(self):
        '''Print the last button pushed, and when it was pressed. Also
        report what function it wants to call.'''

        if self._call_seq:
            self.parse_seq()

        t_elapsed = time.time() - self.last_button_pressed_at
        func = self.button_functions[self.last_button]


        if self._call_func:
            print("--------------------------------------------------")
            print("Button sequence is {}".format(self.button_seq))
            print("The last button pressed was {}, {:.3f}s ago".format(self.last_button, t_elapsed))
            print("This button wants to call the function: {}".format(func.__name__))
            print("--------------------------------------------------")
            if self._is_polling:
                threading.Thread(target=func).start()
            self._call_func = False

        if self._is_polling:
            threading.Timer(self.POLLING_RATE, self.parse_button).start()

    def parse_seq(self):
        '''Check the button sequence. If we want to do something, do it '''
        if self.button_seq == self.konami:
            threading.Thread(target=self.konami_function).start()
            self._call_seq = False
            self._call_func = False

        if self.button_seq == self.kill_seq:
            self.quit()
            self._call_seq = False
            self._call_func = False

        if self.button_seq == self.cummy:
            self.play_cummy()

        if self.button_seq == self.voyager:
            self.play_voyager()

    def play_voyager(self):
        '''play a voyager file'''
        fnames = Path("AUDIO_FILES").glob("VOYAGER/*.wav")
        try:
            playme = random.choice(fnames)
        except: pass

        self.play_clip(playme)

    def play_cummy(self):
        '''play a cum file'''
        fnames = Path('.').glob("AUDIO_FILES/CUM/*.wav")
        try:
            playme = random.choice(fnames)
        except:
            return

        # Stop current playback
        self.interrupt_playback()

        self.play_clip(playme)

    def not_implimented(self):
        # make this flash an LED or something, just to show the user something was noticed?
        print("Button does nothing :(")

    def konami_function(self):
        print("KONAMI")

    def validate_phone_number(self, num):
        '''Call to API to check if the number entered is valid'''
        URL = "http://apilayer.net/api/validate"

        URL += "?access_key={}".format(self.NUMVERIFY_APIKEY)
        URL += "&number={}".format(num)
        URL += "&country_code=GB"
        URL += "&format=1" # return JSON

        resp = requests.post(URL)
        packet = resp.json()
        print(packet)

        isvalid = packet['valid']

        return isvalid

    def handset_lifted(self):
        self._handset_was_up = True
        print("Handset lifted!")
        threading.Thread(target=self.play_random).start()

    def start_recording(self):
        self.interrupt_playback()
        print("#####################################################")
        print("                Starting a recording")
        print("#####################################################")
        self.make_recording()

    def make_recording(self):
        '''Stop current playback, if it's running, play the 'please record a
        message' mesasge, and start recording.'''

        # Get the name of the new audio file to create
        audio_files = Path('.').glob("**/RECORDED/*.wav")
        audio_files = [str(p) for p in audio_files]
        max_num = 0
        for a in audio_files:
            try:
                a = os.path.split(a)[1]
                a = a.replace('.wav', '')
                print(a)
                a = int(a)
                if a > max_num:
                    max_num = a
            except: pass

        new_file = "{:05d}.wav".format(max_num + 1)
        new_file = os.path.join("AUDIO_FILES", "RECORDED", new_file)
        print("Making a new file: {}".format(new_file))

        self.play_clip("AUDIO_FILES/RECORDED/Intro.wav", interruptible=False)

        self.record_clip(new_file)

    def record_clip(self, oname):
        self._playing = True
        self._recording = True

        # Init the audio handler
        p = pyaudio.PyAudio()

        # Start recording, until the cradle is activated
        stream = p.open(
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
            while True:
                if self._interrupt:
                    print("Interrupted recording")
                    break
                data = stream.read(self.CHUNK)
                frames.append(data)
        except Exception as e:
            print("Crashed during recording")
            print(e)


        print("Done recording...")

        # Close my stuff
        stream.stop_stream()
        stream.close()

        if frames != []:
            # Reconstruct the wav, for saving
            waveFile = wave.open(oname, 'wb')
            waveFile.setnchannels(self.CHANNELS)
            waveFile.setsampwidth(p.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)

            waveFile.writeframes(b''.join(frames))
            waveFile.close()

        p.terminate()

        # No longer busy
        self._playing = False
        self._recording = False
        self._interrupt = False

        print("Finished saving recording to {}".format(oname))

    def play_clip(self, playme, interruptible=True):
        if self._playing:
            print("Already playing")
            return

        print("Starting a new playback")

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True

        time.sleep(2)

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

        try:
            while data:
                if self._interrupt:
                    print("Interrupted playback")
                    break
                stream.write(data)
                data = f.readframes(self.CHUNK)
        except Exception as e:
            print("Crashed during Playback")
            print(e)

        print("Done with playback!")

        #stop stream
        stream.stop_stream()
        stream.close()
        f.close()

        #close PyAudio
        p.terminate()

        # I'm no longer playing.
        self._playing = False
        self._interrupt = False
        print("Finished playback")

    def get_audio_files(self):
        fnames = Path('.').glob("**/*.wav")

        audio_files = []
        for a in fnames:
            a = str(a)
            flag = False
            for banned in self.FORBIDDEN_AUDIO:
                if banned in a:
                    flag = True
            if not flag:
                audio_files.append(a)

        print("I found {} audio files:".format(len(audio_files)))
        for fn in audio_files:
            print("- {}".format(fn))

        return audio_files

    def play_random(self):
        files = self.get_audio_files()

        playme = random.choice(files)
        print("Playing file:\n{}\n".format(playme))

        self.play_clip(playme)
