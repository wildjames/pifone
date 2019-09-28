import os
import time
import wave
from pathlib import Path
from threading import Thread, Timer

import gpiozero
import numpy as np
import pyaudio
from numpy import random
from requests import post


class Listener():
    # Fixed variables
    AUDIO_FILES_LOCATION = "/home/pi/pifone"
    NUMVERIFY_APIKEY = "55d54bda772465a9979d9c78ca1b7313"

    CHUNK = 512
    POLLING_RATE = 0.05 #s
    VOLUME = 1.0
    RATE = 44100

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    FORBIDDEN_AUDIO = [
        'Intro',
        'Thanks',
        '/VOYAGER',
        '/CUM',
        '/RECORDED.OLD',
        'mortal_kombat',
        'operator'
    ]

    def __init__(self):
        # Set up audio player
        self.player = pyaudio.PyAudio()
        print(self.player.get_device_count())
        for dev_index in range(self.player.get_device_count()):
            info = self.player.get_device_info_by_index(dev_index)
            if info['name'] == 'USB Audio Device: - (hw:1,0)':
                self.DEVICE_INDEX = dev_index
        print("The USB sound card is device, {}".format(self.DEVICE_INDEX))

        # I/O Pin setup
        self.cradle_pin  = gpiozero.DigitalInputDevice(pin=22)
        print("Initialised the cradle input")

        # The buttons are separated into groups.
        # These are one side of the buttons, which will have a voltage applied
        self.grpA_pin = gpiozero.DigitalOutputDevice(pin=12, initial_value=False)
        self.grpB_pin = gpiozero.DigitalOutputDevice(pin=11, initial_value=False)
        self.grpC_pin = gpiozero.DigitalOutputDevice(pin=10, initial_value=False)
        self.grpD_pin = gpiozero.DigitalOutputDevice(pin=9, initial_value=False)
        print("Initialised Output pins")

        # These are the input pins. I need to check which circuit is closed.
        self.outA_pin = gpiozero.DigitalInputDevice(pin=8)
        self.outB_pin = gpiozero.DigitalInputDevice(pin=7)
        self.outC_pin = gpiozero.DigitalInputDevice(pin=6)
        self.outD_pin = gpiozero.DigitalInputDevice(pin=5)
        self.inpins = [self.outA_pin, self.outB_pin, self.outC_pin, self.outD_pin]
        print("Initialised Input pins")

        # Keys for reconstructing the dialtones
        self.button_tones = {
            'tone': [2, 2],
            'redial': [0, 3],
            '*': [3, 0],
            '#': [3, 2],
            0:   [3, 1],
            1:   [0, 0],
            2:   [0, 1],
            3:   [0, 2],
            4:   [1, 0],
            5:   [1, 1],
            6:   [1, 2],
            7:   [2, 0],
            8:   [2, 1],
            9:   [2, 2],
        }

        self.button_functions = {
            None:     self.not_implimented,
            'redial': self.start_recording,
            '#': self.play_random,
            '*': self.store_phone_number,
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

        self.konami   = [5, 5, '*', '*', 8, 2, 8, 2, '#', '*', 'redial']
        self.kill_seq = [4, 2, 8, 6]
        self.cummy    = [2, 1, 0, 8]
        self.voyager  = [1, 9, 7, 7]

        # Playback flag
        self._playing = False
        self._interrupe = False

        # Cradle handling flags
        self._handset_is_up = False
        self._handset_was_up = False

        # Button handling flags
        self.last_button = None
        self.last_button_pressed_at = time.time()
        self.button_seq = []
        self._call_seq = True
        self._call_func = True

        os.chdir(self.AUDIO_FILES_LOCATION)
        print("Initialised successfully!")

        # Thread(target=self.poll_buttons).start()

    def start(self):
        '''Start the polling function.'''
        print("OK, GO")
        Timer(self.POLLING_RATE, self.poll_buttons).start()

    def quit(self):
        self.interrupt()
        self.player.terminate()
        exit()

    def play_clip(self, playme, interruptible=True):
        if self._playing:
            print("Already playing")
            return

        print("I want to play the file {}".format(playme))
        print("do I want to be interrupted? {}".format(interruptible))
        print("starting new playback")
        self._playing = True
        self._interrupt = False

        if not os.path.isfile(playme):
            print("File not found!")
            return

        with wave.open(playme, 'rb') as audio_file:
            # Use the existing player to open a playback stream

            fmt = self.player.get_format_from_width(
                audio_file.getsampwidth()
            )

            frames = audio_file.getnframes()
            rate = audio_file.getframerate()
            duration = frames / rate

            print("This file is {:.1f}s long".format(duration))

            stream = self.player.open(
                output_device_index=self.DEVICE_INDEX,
                format=fmt,
                channels=self.CHANNELS,
                rate=rate,
                output=True,
                frames_per_buffer=self.CHUNK
            )

            data = audio_file.readframes(self.CHUNK)

            print("About to start playback...")
            while data and self._handset_is_up and self._playing:
                if self._interrupt:
                    break
                print("Writing stream...", end='\r')
                stream.write(data)
                print("Reading data...", end='\r')
                data = audio_file.readframes(self.CHUNK)
            print()

            print("Done with playback!")

        #stop stream
        stream.stop_stream()
        print("Stopped stream")
        stream.close()
        print("Closed stream")

        # I'm no longer playing.
        self._playing = False
        self._interrupt = False
        print("Finished playback")

    def make_recording(self):
        '''Stop current playback, if it's running, play the 'please record a
        message' mesasge, and start recording.

        fresh recordings are numbered in ascending order
        '''

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

        self.play_clip("AUDIO_FILES/Intro.wav", interruptible=False)

        self.record_clip(new_file)

    def record_clip(self, oname):
        self._playing = True
        self._recording = True

        # Play a tone
        if self._handset_is_up:
            self.dialtone('tone')
        else:
            return

        # Start recording, until the cradle is activated
        stream = self.player.open(
            input_device_index=self.DEVICE_INDEX,
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        print("Recording...")
        frames = []

        try:
            while not self._interrupt:
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
            waveFile.setsampwidth(self.player.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)

            waveFile.writeframes(b''.join(frames))
            waveFile.close()

            print("Finished saving recording to {}".format(oname))

        # No longer busy
        self._playing  = False
        self._recording = False
        self._interrupt = False

    def dialtone(self, button, duration=0.1):
        '''Play a dialtone, corresponding to <button>, for <duration> seconds'''
        print("Playing a button tone for {}".format(button))
        volume = self.VOLUME
        fs = self.RATE

        freqs_A = [1209., 1336., 1477., 1633.]
        freqs_B = [697.,  770.,  852.,  941.]

        f_A, f_B = self.button_tones[button]

        f_A = freqs_A[f_A]
        f_B = freqs_B[f_B]

        f = f_A + f_B

        if button == 'tone':
            f = 1400.
        f = float(f)

        # generate samples, note conversion to float32 array
        samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)

        # for paFloat32 sample values must be in range [-1.0, 1.0]
        stream = self.player.open(
            output_device_index=self.DEVICE_INDEX,
            format=pyaudio.paFloat32,
            channels=1,
            rate=fs,
            output=True
        )

        # play. May repeat with different volume values (if done interactively)
        stream.write(volume*samples)

        stream.stop_stream()
        stream.close()

        print("Played a dialtone")

    def poll_buttons(self):
        '''Figure out which buttons have been pressed, and if necessary,
        execute their function'''

        # If the cradle is raised, play is True
        self._handset_is_up = not self.cradle_pin.value
        if not self._handset_is_up and self._handset_was_up:
            print("Handset in cradle")
            self._call_seq = True
            self._handset_was_up = False

            Thread(target=self.interrupt).start()

        if not self._handset_is_up:
            self.button_seq = []
            self._playing = False
            self._playing_cummy = False
            self._interrupt = True

        if not self._handset_was_up and self._handset_is_up:
            Thread(target=self.handset_lifted).start()

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
        outputs = [None, 9, 8, 7]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpB_pin.value = False

        # Check the Third group
        self.grpC_pin.value = True
        outputs = [None, 6, 5, 4]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpC_pin.value = False

        # Check the fourth group
        self.grpD_pin.value = True
        outputs = [None, 3, 2, 1]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                button_pressed = outputs[i]
                break
        self.grpD_pin.value = False

        # If a button was pushed, say so
        if button_pressed is not None:
            if self.last_button is None:
                self._playing_cummy = False
                Thread(target=self.dialtone, args=(button_pressed,)).start()
                self.button_seq.append(button_pressed)
                # Raise a flag to call this button's function, if it has one
                self._call_func = True

        self.last_button = button_pressed
        self.last_button_pressed_at = time.time()

        Thread(target=self.parse_button).start()

        Timer(self.POLLING_RATE, self.poll_buttons).start()
        # time.sleep(self.POLLING_RATE)
        # self.poll_buttons()

    def handset_lifted(self):
        self._handset_was_up = True
        print("Handset lifted!")
        # Thread(target=self.play_random).start()
        self.play_clip('AUDIO_FILES/operator.wav')
        self.dialtone('tone')

    def interrupt(self):
        self._interrupt = True

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
            print("_call_seq: {}".format(self._call_seq))
            print("--------------------------------------------------")
            Thread(target=func).start()
            self._call_func = False

    def parse_seq(self):
        '''Check the button sequence. If we want to do something, do it '''
        if self.button_seq == self.konami:
            self._call_seq = False
            self._call_func = False
            Thread(target=self.konami_function).start()

        if self.button_seq == self.kill_seq:
            self._call_seq = False
            self._call_func = False
            self.quit()

        if self.button_seq == self.cummy:
            self._call_seq = False
            self._call_func = False
            Thread(target=self.play_cummy).start()

        if self.button_seq == self.voyager:
            self._call_seq = False
            self._call_func = False
            Thread(target=self.play_voyager).start()

        if self.button_seq == self.play_recording:
            self._call_seq = False
            self._call_func = False
            Thread(target=self.play_specific_recording).start()

    def start_recording(self):
        self.interrupt()
        print("#####################################################")
        print("                Starting a recording")
        print("#####################################################")
        self.make_recording()

    def get_audio_files(self):
        fnames = Path('.').glob("**/*.wav")

        audio_files = []
        for a in fnames:
            a = str(a)
            flag = True
            for banned in self.FORBIDDEN_AUDIO:
                if banned in a:
                    flag = False
            if flag:
                audio_files.append(a)

        print("I found {} audio files:".format(len(audio_files)))
        for fn in audio_files:
            print("- {}".format(fn))

        return audio_files

    def not_implimented(self):
        # make this flash an LED or something, just to show the user something was noticed?
        print("Button does nothing :(")

    def play_random(self):
        self.interrupt()
        print("Getting audio files")
        files = self.get_audio_files()

        playme = random.choice(files)
        print("Playing file:\n{}\n".format(playme))

        self.play_clip(playme)

    def validate_phone_number(self, num):
        '''Call to API to check if the number entered is valid'''
        URL = "http://apilayer.net/api/validate"

        URL += "?access_key={}".format(self.NUMVERIFY_APIKEY)
        URL += "&number={}".format(num)
        URL += "&country_code=GB"
        URL += "&format=1" # return JSON

        resp = post(URL)
        packet = resp.json()

        isvalid = packet['valid']

        return isvalid

    def store_phone_number(self):
        numbers = [0,1,2,3,4,5,6,7,8,9]
        num = [str(num) for num in self.button_seq if num in numbers]
        num = ''.join(num)

        print("Validating the number: {}".format(num))
        isValid = self.validate_phone_number(num)
        print("Is it valid?: {}".format(isValid))

        if isValid:
            with open("numbers.txt", 'a+') as f:
                f.write("{}\n".format(num))
        print("Done!\n")

    def play_voyager(self):
        '''play a voyager file'''
        self.interrupt()
        fnames = [str(f) for f in Path(".").glob("**/VOYAGER/*.wav")]
        if fnames == []:
            print("No files found")
            return

        playme = random.choice(fnames)
        self.play_clip(playme)

    def play_cummy(self):
        '''play a cum file'''
        self._playing_cummy = True
        print(os.listdir('AUDIO_FILES'))
        fnames = [str(f) for f in Path('.').glob("**/CUM/*")]
        print("Found {:d} drops of CUM".format(len(fnames)))
        if fnames == []:
            return

        # Stop current playback
        self.interrupt()

        while self._handset_is_up and not self._playing and self._playing_cummy:
            playme = random.choice(fnames)
            self.play_clip(playme)
        self._playing_cummy = False

    def konami_function(self):
        self.interrupt()
        self.play_clip('AUDIO_FILES/mortal_kombat.wav')

    def play_specific_recording(self):
        number = self.button_seq
        number = [n for n in number if n in [0,1,2,3,4,5,6,7,8,9]]

        fname = "{:0d5}.wav".format(number)
        fname = os.path.join('AUDIO_FILES', 'RECORDED', fname)

        self.play_clip(fname)
