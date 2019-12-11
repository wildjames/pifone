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
    print("Interrupt sent\n   -> Music should STOP")
    time.sleep(5)

    print("Restarting playback\n   -> Music should BEGIN")
    dic.start("play_file", fname)
    time.sleep(5)

    print("Trying to start playback over previous playback\n   -> Music should CONTINUE, NOTHING should begin")
    dic.start('play_random')
    time.sleep(10)

    dic.interrupt_playback()
    print("Termination sent!\n   -> Music should STOP")
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
    time.sleep(3)

    print("Playing TEST.wav")
    dic.start('play_file', 'AUDIO_FILES/RECORDED/TEST.wav')
    time.sleep(10)
    print("Done!")

    time.sleep(3)

    print("Starting playback, then a recording.")
    print("Playback should BEGIN, then when recording starts, playback should STOP")
    dic.start("play_file", 'AUDIO_FILES/DICTAPHONE_DIARIES/VN860028.wav')
    time.sleep(5)
    if os.path.isfile("AUDIO_FILES/RECORDED/TEST2.wav"):
        os.remove("AUDIO_FILES/RECORDED/TEST2.wav")
    dic.start("make_recording", "TEST2.wav")

    time.sleep(10)
    dic.stop_recording()
    print("Recording over")

print("Done testing.")

