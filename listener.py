import pyaudio
import wave
import os
from pathlib import Path
from random import choice

import multiprocessing
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

        # Create blank versions of objects I'll refer to later
        # self.thread = multiprocessing.Process()
        self.thread = threading.Thread()

        return

    def start(self, cmd, *args, **kwargs):
        '''
        Run the given class method, with *args and **kwargs.

        Raises an error if it doesn't exist.
        '''

        if self.thread.is_alive():
            print("Already playing!")
            return

        target = getattr(self, cmd)
        args = args
        kwargs = kwargs

        # self.thread = multiprocessing.Process(
        self.thread = threading.Thread(
            target=target, args=args, kwargs=kwargs,
            daemon=True,
        )
        self.thread.start()

    def play_random(self):
        '''Play a random audio file from my audio_files directory.
        Searches for .wav, recursively
        '''

        if self.LOUD > 3:
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

        # Done recording, raise flag
        self._stop_recording = False

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

        self._stop_playback = False

    def interrupt_playback(self):
        # self.thread.terminate()
        self._stop_playback = True

    def stop_recording(self):
        self._stop_recording = True
        # self.thread.terminate()


class PhoneMonitor(object):
    '''
    This class should listen for two things:
      - Buttons being pressed currently
      - If the handset is lifted or not

    It should also track a few things:
      - Has the button's corresponding function been called already
      - What button sequence has been pushed

    The button sequence should be cleared when the handset is set down.
    '''



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