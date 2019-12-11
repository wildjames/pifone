import time
from listener import Dictaphone
import os


###### TEST THE DICTAPHONE OBJECT ######
test_playback = True
test_recording = True


# Play a test file with the dictaphone
fname = "AUDIO_FILES/mortal_kombat.wav"
dic = Dictaphone(audio_dir='AUDIO_FILES')


#### Playback ####
if test_playback:
    print("Playing a random file...")
    dic.start("play_random")
    time.sleep(5)

    # Interrupt playback
    dic.interrupt_playback()
    print("Interrupt sent - Music should STOP")
    time.sleep(5)

    print("Restarting playback - Music should BEGIN")
    dic.start("play_file", fname)
    time.sleep(5)

    print("Trying to start playback over previous playback - Music should CONTINUE, NOTHING should begin")
    dic.start('play_file', fname)
    time.sleep(10)

    dic.interrupt_playback()
    print("Termination sent! Music should STOP")
    time.sleep(5)


#### Recording ####
if test_recording:
    print("Making a recording in the RECORDED dir, called TEST.wav, 10s long")
    if os.path.isfile("AUDIO_FILES/RECORDED/TEST.wav"):
        os.remove("AUDIO_FILES/RECORDED/TEST.wav")

    dic.start('make_recording', 'TEST.wav')
    print("Started!")

    time.sleep(10)
    dic.stop_recording()
    print("Done!")

print("Done testing.")

