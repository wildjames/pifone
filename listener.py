import pyaudio
import wave
import os
from pathlib import Path
from random import choice

import threading

# Only needed for debugging
import time
from pprint import pprint



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
        '''Play the audio file, fname.
        If something is already playing, stop it.

        Inputs
        ------
          - fname, str:
            - The file to be played
        '''

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
            print("Setting _stop_playback to False")
        self._stop_playback = False

    def interrupt_playback(self):
        self._stop_playback = True

    def stop_recording(self):
        self._stop_recording = True

    def stop(self):
        self.interrupt_playback()
        self.stop_recording()

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
    POLLING_RATE = 0.5 #s
    LOUD = 3

    def __init__(self, dummy_mode=False):
        self.dummy_mode = dummy_mode
        if dummy_mode:
            self.dummy_pressed = None

        self.last_pushed = None
        self.call_button = None
        self.sequence = []

        self._polling = False

    def poll_buttons(self):
        '''
        Tests each button for being pushed, and sets the internal list of
        currently pushed buttons
        '''
        if not self._polling:
            return

        # Default to None buttons pushed
        self.currently_pushed = None

        if self.dummy_mode:
            self.currently_pushed = self.dummy_pressed

            if self.LOUD > 3:
                print("Button being pushed is: {}".format(self.currently_pushed))
        else:
            print("I need to check each of the pins to see if they're telling me a button has been pushed.")
            print("First check that the handset is up or down. If it's up, and wasn't before, set currently_pushed = 'handset_up'")
            print("If the handset is NOT up, set currently_pushed = 'handset_down'")
            print("If currently_pushed is still None, check the buttons for depression")
            print("If one has, set currently pushed to it's name")

        # If the handset isn't up, and we've not recorded that it's been lifted, stop now
        if 'handset_up' not in self.sequence:
            if self.currently_pushed != 'handset_up':
                self.clear_sequence()
                threading.Timer(self.POLLING_RATE, self.poll_buttons).start()
                return

        if self.currently_pushed == 'handset_down':
            self.clear_sequence()


        # Actually handle the button, if I need to
        if self.last_pushed != self.currently_pushed:
            if self.currently_pushed != None:
                self.call_button = self.currently_pushed
                self.sequence.append(self.currently_pushed)

                if self.LOUD > 2:
                    print("I need to call the function for button {}!".format(self.call_button))
                    print("My sequence is now {}".format(self.sequence))

        # Update the last pushed button
        self.last_pushed = self.currently_pushed

        # Start a timer for the next call
        threading.Timer(self.POLLING_RATE, self.poll_buttons).start()

    def clear_sequence(self):
        '''Clear the recording of which buttons have been pushed'''
        self.sequence = []

    def called_button(self):
        '''Reset the call_button flag, telling the signaller that the event has been handled'''
        self.call_button = None

    def start(self):
        '''Start the poll_buttons method. That function calls itself, so runs indefinitely.'''
        self._polling = True
        threading.Timer(self.POLLING_RATE, self.poll_buttons).start()

    def stop(self):
        self._polling = False


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
    POLLING_RATE = 1.0
    _polling = False
    loud = 4

    def __init__(self, audio_dir='.', debug=0):
        '''
        Start up my Dictaphone and Signaller objects, which will handle lower level stuff.
        '''

        self.dictaphone = Dictaphone(audio_dir)
        self.monitor = PhoneMonitor(dummy_mode=True)

        self.button_functions = {
            'B1': self.not_implimented,
            'B2': self.not_implimented,
            'B3': self.not_implimented,
            'B4': self.not_implimented,
            'handset_up': self.play_intro,
            'handset_down': self.handset_replaced,
        }

    def start(self):
        '''Start up the monitor, and myself checking for inputs'''
        if not self._polling:
            # Start my monitor first
            self.monitor.start()

            # Then start myself, checking the monitor
            self._polling = True
            threading.Thread(target=self.poll_monitor).start()
        else:
            print("Cannot start when I'm already running!")

    def stop(self):
        '''Stop myself, and my monitor's polling, and my dictaphone's playback'''
        self._polling = False
        self.monitor.stop()
        self.dictaphone.stop()

    def poll_monitor(self):
        '''If the monitor has picked up on a button that must be evaluated, do that'''
        # Only execute the button if the handset_up is recorded in the sequence
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

