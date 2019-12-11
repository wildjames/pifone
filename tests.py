import time
from listener import Dictaphone



# Play a test file with the dictaphone
fname = "AUDIO_FILES/mortal_kombat.wav"
dic = Dictaphone()
dic.start("play_file", fname)
time.sleep(5)

# Interrupt playback
dic.interrupt_playback()
print("Interrupt sent")
time.sleep(5)

print("Restarting playback...")
dic.start("play_file", fname)
time.sleep(5)

print("Trying to start playback over previous playback...")
dic.start('play_file', fname)
time.sleep(10)

dic.interrupt_playback()
print("Termination sent!")
time.sleep(5)




print("Done testing.")

