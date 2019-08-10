import fnmatch
import os
import random

import pyaudio
import wave

import threading
try:
    import gpiozero
except: pass



class Listener():
    # Playback, file reading, polling settings
    CHUNK = 1024
    POLLING_RATE = 0.5 #s
    play = False
    _playing = False
    _recording = False

    # Recording settings
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    try:
        pin17 = gpiozero.DigitalOutputDevice(pin=17, initial_value=True)
        pin27 = gpiozero.DigitalInputDevice(pin=27)
        pin22 = gpiozero.DigitalInputDevice(pin=22)
        print("Successfully initialised cradle to pins 17, 27, 22")

        pin5   = gpiozero.DigitalOutputDevice(pin=5, initial_value=True)
        pin6   = gpiozero.DigitalInputDevice(pin=6)
        pin13  = gpiozero.DigitalInputDevice(pin=13)
        rpi = True
    except:
        rpi = False
        print("Not running on a raspberry pi!")

    def __init__(self):
        threading.Timer(self.POLLING_RATE, self._listen).start()

    def _listen(self):
        # os.system("clear")
        print("Current values:")
        print("Currently playing?  {}".format(self._playing))
        print("play: {}".format(self.play))
        if self.rpi:
            print("pin17:   {}".format(self.pin17.value))
            print("pin27:   {}".format(self.pin27.value))
            print("pin22:     {}".format(self.pin22.value))

            self.play = self.pin27.value
            self.record = self.pin6.value

        if self._playing == False and self.play == True:
            threading.Thread(target=self.play_random).start()

        if self._recording == False and self.play and self.record:
            threading.Thread(target=self.make_recording).start()


        threading.Timer(self.POLLING_RATE, self._listen).start()

    def make_recording(self):
        self._playing = True
        self._recording = True

        audio_files = [0]
        for root, dirnames, filenames in os.walk("AUDIO_FILES/RECORDED/"):
            for filename in fnmatch.filter(filenames, "*.wav"):
                fname = filename.replace('.wav', '')
                audio_files.append(int(fname))
        new_file = "{:010d}.wav".format(max(audio_files) + 1)
        new_file = os.path.join("AUDIO_FILES", "RECORDED", new_file)
        print("Making a new file: {}".format(new_file))

        # audio = pyaudio.PyAudio()

        # Start recording, until the cradle is activated
        # stream = audio.open(
        #     format=self.FORMAT,
        #     channels=self.CHANNELS,
        #     rate=self.RATE,
        #     input=True,
        #     frames_per_buffer=self.CHUNK
        # )
        print("Recording...")
        # frames = []

        while self.play:
            # data = stream.read(self.CHUNK)
            # frames.append(data)
            print("  - Making another chunk...")

        print("Finished recording")

        # # Close my stuff
        # stream.stop_stream()
        # stream.close()

        # audio.terminate()

        # # Reconstruct the wav, for saving
        # waveFile = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        # waveFile.setnchannels(self.CHANNELS)
        # waveFile.setsampwidth(audio.get_sample_size(self.FORMAT))
        # waveFile.setframerate(self.RATE)
        # waveFile.writeframes(b''.join(frames))
        # waveFile.close()

        # No longer busy
        self._playing = False

    def play_clip(self, playme):
        if self._playing:
            return

        print("Starting a new playback")

        # Now that I'm playing, make sure we don't start another playback
        self._playing = True
        self._recording = False

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

        #play stream
        while data and self.play:
            stream.write(data)
            data = f.readframes(self.CHUNK)

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
        for root, dirnames, filenames in os.walk("AUDIO_FILES/"):
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

#     l.play_random()