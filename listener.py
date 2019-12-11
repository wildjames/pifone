import pyaudio
import wave
import os

import multiprocessing

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
    CHUNKSIZE = 1024
    _stop_playback = False

    def __init__(self, chunk_size=None, **kwargs):
        '''Set up the dictaphone's audio stream'''

        if chunk_size is not None:
            self.CHUNKSIZE = chunk_size

        self.audio_thread = multiprocessing.Process()

        return

    def start(self, cmd, *args, **kwargs):
        '''
        Run the given class method, with *args and **kwargs.

        Raises an error if it doesn't exist.
        '''

        if self.audio_thread.is_alive():
            print("Already playing!")
            return

        target = getattr(self, cmd)
        args = args
        kwargs = kwargs

        self.audio_thread = multiprocessing.Process(
            target=target, args=args, kwargs=kwargs,
            daemon=True,
        )
        self.audio_thread.start()

    def play_file(self, fname):
        '''Play the audio file, fname.
        If something is already playing, stop it.

        Inputs
        ------
          - fname, str:
            - The file to be played
        '''
        self.audio_stream = pyaudio.PyAudio()
        print("fname:\n'{}'".format(fname))
        exists = os.path.isfile(fname)
        print("Does it exist? {}".format("Yes" if exists else "No"))
        audio_file = wave.open(fname, 'rb')

        # Get the format of the audio file
        width = audio_file.getsampwidth()
        fmt = self.audio_stream.get_format_from_width(width)
        n_channels = audio_file.getnchannels()
        rate = audio_file.getframerate()

        stream = self.audio_stream.open(
            format=fmt,
            channels=n_channels,
            rate=rate,
            output=True,
        )

        data = audio_file.readframes(self.CHUNKSIZE)
        while data != '' and not self._stop_playback:
            stream.write(data)
            data = audio_file.readframes(self.CHUNKSIZE)

        stream.stop_stream()
        stream.close()

        self.audio_stream.terminate()

        return

    def interrupt_playback(self):
        self.audio_thread.terminate()



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