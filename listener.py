import os
import threading
# Only needed for debugging
import time
import wave
from pathlib import Path
from pprint import pprint
from random import choice

import gpiozero
import pyaudio


class Dictaphone(object):
    '''
    This class acts as a dictaphone (obviously). It should have the following capabilities:
      - play a recorded message
      - record a new message

    To make it run in the background, which we definitely want, we need to
    have it play stuff in a new thread.

    How hard can that be?

    Inputs
    ------
      - chunk_size, int:
        - The number of bytes of each playback chunk
    '''
    RATE = 44100
    CHUNKSIZE = 1024
    N_CHANNELS = 1
    FORMAT = pyaudio.paInt16

    _stop_playback = False
    _stop_recording = False

    LOUD = 4

    def __init__(self, audio_dir='.', rate=None, rec_format=None, chunk_size=None, n_channels=None, **kwargs):
        '''Set up the dictaphone's audio stream'''

        if rate is not None:
            self.RATE = rate
        if chunk_size is not None:
            self.CHUNKSIZE = chunk_size
        if n_channels is not None:
            self.N_CHANNELS = n_channels
        if rec_format is not None:
            self.FORMAT = rec_format

        self.audio_dir = audio_dir

        # A list of my threads. This is where my dead threads accumulate...
        self.threads = []

        # # TODO: When all threads are dead, reset the above list to free memory.
        # # Removing them from the list should delete all references to them,
        # # then the garbage collector can free the stuff as normal
        # self.thread_garbage_collector = threading.Timer(
        #     target=self._reset_threadlist
        # )

        return

    def start(self, cmd, *args, **kwargs):
        '''
        Run the given class method, with *args and **kwargs.

        Raises an error if it doesn't exist.
        '''

        target = getattr(self, cmd)
        args = args
        kwargs = kwargs

        # self.thread = multiprocessing.Process(
        self.threads.append(
            threading.Thread(
                target=target, args=args, kwargs=kwargs,
                daemon=True,
            )
        )
        self.threads[-1].start()

    def play_random(self):
        '''Play a random audio file from my audio_files directory.
        Searches for .wav, recursively
        '''

        if self.LOUD > 4:
            print("Files in my audio_dir")
        files = []
        for filename in Path(self.audio_dir).rglob('*.wav'):
            files.append(str(filename))

        if self.LOUD > 3:
            for f in files:
                print(f)

        fname = choice(files)

        self.play_file(fname)

    def make_recording(self, fname=''):
        '''
        Create a recording in the directory: <self.audio_dir>/RECORDED
        with the filename specified. If none is given, the
        '''
        rec_dir = os.path.join(self.audio_dir, 'RECORDED')

        if fname == '':
            # get the highest filename number in the recording dir
            max_num = 0
            for filename in Path(rec_dir).rglob('*.wav'):
                filename = os.path.split(filename)[-1]
                file_num = os.path.splitext(filename)[0]

                if file_num.isdigit():
                    file_num = int(file_num)
                    if file_num >= max_num:
                        max_num = file_num + 1

            oname = "{:>04d}.wav".format(max_num)
            oname = os.path.join(rec_dir, oname)

        else:
            oname = os.path.join(rec_dir, fname)
        if os.path.isfile(oname):
            print("File '{}' already exists! Not recording over it.".format(oname))
            return

        # I'll overwrite the process termination to wait for this flag to become True,
        # so that my file writing always works properly
        self._stop_recording = False
        self._stop_playback = True

        if self.LOUD > 0:
            print("Making a recording, saving to {}".format(oname))

        # Open an audio stream for recording
        audio_stream = pyaudio.PyAudio()

        rec_stream = audio_stream.open(
            format=self.FORMAT,
            channels=self.N_CHANNELS,
            rate=self.RATE,
            frames_per_buffer=self.CHUNKSIZE,
            input=True
        )

        # Write the data to a file
        audio_file = wave.open(oname, 'wb')
        audio_file.setnchannels(self.N_CHANNELS)
        audio_file.setsampwidth(audio_stream.get_sample_size(self.FORMAT))
        audio_file.setframerate(self.RATE)

        # TODO:  (SAFE ON RPI???)
        # Record all the frames we want, writing them as we go
        while not self._stop_recording:
            try:
                frame = rec_stream.read(self.CHUNKSIZE)
                audio_file.writeframes(frame)
            except:
                break

        # Close the stream
        rec_stream.stop_stream()
        rec_stream.close()
        audio_stream.terminate()
        audio_file.close()

        if self.LOUD > 0:
            print("Recording Finished, setting flags to reset interrupts")
        # Done recording, raise flag.
        self._stop_recording = False
        # Playback can also resume now
        self._stop_playback = False

    def play_file(self, fname):
        '''Play the audio file, fname. Relative path to where the script was run from.
        If something is already playing, stop it.

        Inputs
        ------
          - fname, str:
            - The file to be played
        '''

        print("stop playback? {}".format(self._stop_playback))

        # Open audio stream for reading
        audio_stream = pyaudio.PyAudio()

        # Check the audio file exists. If it does, open it for reading
        exists = os.path.isfile(fname)
        if self.LOUD > 2:
            print("fname:\n'{}'".format(fname))
            print("Does it exist? {}".format("Yes" if exists else "No"))
        if not exists:
            return
        audio_file = wave.open(fname, 'rb')

        # Get the format of the audio file, number of channels (L,R speakers?), and framerate
        width = audio_file.getsampwidth()
        fmt = audio_stream.get_format_from_width(width)
        n_channels = audio_file.getnchannels()
        rate = audio_file.getframerate()

        # Begin stream. This gets written to like a sdtout, only it comes
        # out of your speakers not your terminal
        stream = audio_stream.open(
            format=fmt,
            channels=n_channels,
            rate=rate,
            output=True,
        )

        # Loop through, reading the data and playing it.
        data = audio_file.readframes(self.CHUNKSIZE)
        while data != '' and not self._stop_playback:
            stream.write(data)
            data = audio_file.readframes(self.CHUNKSIZE)

        # close stuff gracefully.
        stream.stop_stream()
        stream.close()
        audio_stream.terminate()

        if self.LOUD > 3:
            print("Finished with playback")
            print("Setting _stop_playback to False")
        self._stop_playback = False

    def enable_playback(self):
        '''Set the flag to enable playback'''
        self._stop_playback = False
        self._stop_recording = False

    def interrupt_playback(self):
        '''Stop playback'''
        self._stop_playback = True

    def stop_recording(self):
        '''Stop recording'''
        self._stop_recording = True

    def stop(self):
        '''Stops both recording, and playback'''
        print("Stop all signal recieved")
        self.interrupt_playback()
        self.stop_recording()
        time.sleep(10*self.CHUNKSIZE/self.RATE)

class PhoneMonitor(object):
    '''
    This class should listen for two things:
      - Buttons being pressed currently
      - If the handset is lifted or not (this is just another button)

    It should also track a few things:
      - Has the button's corresponding function been called already
      - What button sequence has been pushed

    The button sequence should be cleared when the handset is set down.
    '''
    POLLING_RATE = 0.05
    LOUD = 3

    def __init__(self, handset_pin=22, dummy_mode=False):
        if dummy_mode:
            from gpiozero.pins.mock import MockFactory
            gpiozero.Device.pin_factory = MockFactory()

        # The buttons are separated into groups.
        # These are one side of the buttons, which will have a voltage applied
        self.grpA_pin = gpiozero.DigitalOutputDevice(pin=12, initial_value=False)
        self.grpB_pin = gpiozero.DigitalOutputDevice(pin=11, initial_value=False)
        self.grpC_pin = gpiozero.DigitalOutputDevice(pin=10, initial_value=False)
        self.grpD_pin = gpiozero.DigitalOutputDevice(pin=9, initial_value=False)
        print("Initialised Output pins")

        # These are the input pins. I need to check which circuit is closed.
        self.outA_pin = gpiozero.DigitalInputDevice(pin=8)
        self.outB_pin = gpiozero.DigitalInputDevice(pin=7)
        self.outC_pin = gpiozero.DigitalInputDevice(pin=6)
        self.outD_pin = gpiozero.DigitalInputDevice(pin=5)
        self.inpins = [self.outA_pin, self.outB_pin, self.outC_pin, self.outD_pin]
        print("Initialised Input pins")

        # This variable holds the name of a button if it's function needs to be called
        self.call_button = None
        # Last button that was pushed
        self.last_button = None
        # Button press history, since handset was raised
        self.sequence = []

        self._polling = False

        # True only while the handset is up
        self._handset_raised = False

        self.handset_button = gpiozero.Button(handset_pin, pull_up=False)
        self.handset_button.when_pressed = self.handset_down
        self.handset_button.when_released = self.handset_up

        if dummy_mode:
            self.mock_pins = []
            self.mock_pins.append(gpiozero.Device.pin_factory.pin(handset_pin))
            for btn_pin in [8,7,6,5]:
                self.mock_pins.append(
                    gpiozero.Device.pin_factory.pin(btn_pin)
                )
                print("Created dummy pin {}".format(btn_pin))

        threading.Thread(target=self.poll_buttons, daemon=True).start()

    def handset_up(self):
        print("Handset rasied. Now accepting button presses")
        self._handset_raised = True

    def handset_down(self):
        print("Handset replaced. Resetting sequence, and no longer accepting buttons")
        self._handset_raised = False
        self.clear_sequence()

    def clear_sequence(self):
        '''Clear the recording of which buttons have been pushed'''
        self.sequence = []

    def called_button(self):
        '''Reset the call_button flag, telling the signaller that the event has been handled'''
        self.call_button = None

    def ping_buttons(self):
        # Check the first button group
        self.grpA_pin.value = True
        outputs = ['redial', 'hash', 0, 'star']
        for i, pin in enumerate(self.inpins):
            if pin.value:
                self.grpA_pin.value = False
                return outputs[i]
        self.grpA_pin.value = False

        # Check the second group
        self.grpB_pin.value = True
        outputs = [None, 9, 8, 7]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                self.grpB_pin.value = False
                return outputs[i]
        self.grpB_pin.value = False

        # Check the Third group
        self.grpC_pin.value = True
        outputs = [None, 6, 5, 4]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                self.grpC_pin.value = False
                return outputs[i]
        self.grpC_pin.value = False

        # Check the fourth group
        self.grpD_pin.value = True
        outputs = [None, 3, 2, 1]
        for i, pin in enumerate(self.inpins):
            if pin.value:
                self.grpD_pin.value = False
                return outputs[i]
        self.grpD_pin.value = False

        return None

    def poll_buttons(self):
        '''Figure out which buttons have been pressed, and set the 'call me' variable'''
        ############################################################
        # # # # Check if any of the buttons have been pushed # # # #
        ############################################################
        if not self._handset_raised:
            return

        button_pressed = self.ping_buttons()

        # If a button was pushed, say so
        if button_pressed is not None:
            print("last button pressed was {}".format(self.last_button))
            if self.last_button is None:
                print("Detected button {}".format(button_pressed))
                # threading.Thread(target=self.dialtone, args=(button_pressed,)).start()
                self.sequence.append(button_pressed)
                # Raise a flag to call this button's function, if it has one
                self.call_button = button_pressed
        else:
            print("No button currently pressed")

        # Update the last button to be pushed
        self.last_button = button_pressed

        threading.Timer(self.POLLING_RATE, self.poll_buttons).start()


class Phone(object):
    '''
    This class holds all the bits for the phone, and commands them all.

    It should be able to do the following:
      - When the handset is lifted, start the intro clip playing
      - When a button is pushed, play the corresponding DTMF tone
      - When the user presses the correct button, play a random old recording
      - When the user presses the correct button, start making a new recording
      - When the user presses the correct button, play the most recent recording
      - When the handset is replaced, stop all playback and clear the button sequence

    This should all be able to handle stuff happening asyncronously - the user
    can press a button during playback, and a tone should still play OVER the
    existing stream.
    '''
    POLLING_RATE = 0.1
    _polling = False
    loud = 4

    def __init__(self, audio_dir='.', debug=0):
        '''
        Start up my Dictaphone and Signaller objects, which will handle lower level stuff.
        '''

        self.dictaphone = Dictaphone(audio_dir)
        self.monitor = PhoneMonitor(dummy_mode=True)

        self.button_functions = {
            'GPIO1': self.begin_recording,
            'GPIO2': self.play_random,
            'GPIO3': self.not_implimented,
            'GPIO4': self.not_implimented,
            'GPIO5': self.play_intro,
            'GPIO6': self.not_implimented,
        }

    def start(self):
        '''Start up the monitor, and myself checking for inputs'''
        if not self._polling:
            # Start myself checking the monitor
            self._polling = True
            threading.Thread(target=self.poll_monitor).start()
        else:
            print("Cannot start when I'm already running!")

    def stop(self):
        '''Stop myself, and my monitor's polling, and my dictaphone's playback'''
        self._polling = False
        self.dictaphone.stop()

    def poll_monitor(self):
        '''If the monitor has picked up on a button that must be evaluated, do that'''
        # Only execute the button if the handset_up is recorded in the sequence
        if self.monitor._handset_raised:
            if self.monitor.call_button is not None:
                func = self.button_functions[self.monitor.call_button]
                print("I need to call function {}".format(func.__name__))

                threading.Thread(target=func).start()
                self.monitor.called_button()

        if self._polling:
            threading.Timer(self.POLLING_RATE, self.poll_monitor).start()

    def not_implimented(self):
        '''Placeholder.'''
        print("I wanted to call a function, but it has not been implimented yet.")

    def handset_replaced(self):
        '''
        The phone's handset has been replaced.
        Clear the button sequence, and stop any playback or recording.
        '''
        if self.loud > 0:
            print("Handset replaced! Stopping playback")
        # The button sequence is reset
        self.monitor.clear_sequence()
        # Playback and recording must stop
        self.dictaphone.stop()

    def play_intro(self):
        self.dictaphone.start("play_file", "AUDIO_FILES/mortal_kombat.wav")

    def begin_recording(self):
        self.dictaphone.start('make_recording')

    def play_random(self):
        self.dictaphone.stop()
        self.dictaphone.start('play_random')
