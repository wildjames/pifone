import pyaudio
import wave
import os

class Dictaphone(object):
    '''
    This class acts as a dictaphone (obviously). It should have the following capabilities:
      - play a recorded message
      - record a new message

    How hard can that be?

    Inputs
    ------
      - chunk_size, int:
        - The number of bytes of each playback chunk
    '''
    CHUNKSIZE = 1024

    def __init__(self, chunk_size=None):
        '''Set up the dictaphone's audio stream'''

        if chunk_size is not None:
            self.CHUNKSIZE = chunk_size

        self.audio_stream = pyaudio.PyAudio()

        return

    def play_file(self, fname):
        '''Play the audio file, fname.
        If something is already playing, stop it.

        Inputs
        ------
          - fname, str:
            - The file to be played
        '''
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
        while data != '':
            stream.write(data)
            data = audio_file.readframes(self.CHUNKSIZE)

        stream.stop_stream()
        stream.close()

        return

    def terminate(self):
        '''Gracefully close the stream'''
        self.audio_stream.terminate()

        return

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