import time
from listener import Dictaphone

# Play a test file with the dictaphone
fname = "AUDIO_FILES/mortal_kombat.wav"
dic = Dictaphone()
dic.play_file(fname)

time.sleep(5)
dic.interrupt = True
print("Interrupt sent")
time.sleep(3)

print("Pass!")

