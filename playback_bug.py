import os
import wave
import pyaudio

fname = 'AUDIO_FILES/mortal_kombat.wav'

# Open audio stream for reading
audio_stream = pyaudio.PyAudio()

# Check the audio file exists. If it does, open it for reading
exists = os.path.isfile(fname)
if not exists:
    exit()
audio_file = wave.open(fname, 'rb')

# Get the format of the audio file, number of channels (L,R speakers?), and framerate
width = audio_file.getsampwidth()
fmt = audio_stream.get_format_from_width(width)
n_channels = audio_file.getnchannels()
rate = audio_file.getframerate()
CHUNKSIZE = 1024

# Begin stream. This gets written to like a sdtout, only it comes
# out of your speakers not your terminal
stream = audio_stream.open(
    format=fmt,
    channels=n_channels,
    rate=rate,
    output=True,
)

data = audio_file.readframes(CHUNKSIZE)
while data:
    stream.write(data)
    data = audio_file.readframes(CHUNKSIZE)

# close stuff gracefully.
stream.stop_stream()
stream.close()
audio_stream.terminate()
