import time
from listener import Dictaphone, PhoneMonitor, Phone
import os


###### TEST THE DICTAPHONE OBJECT ######
test_playback = False
test_recording = False

###### TEST THE SIGNAL SENDER AND RECIEVER ######
test_signalman = False

###### TEST THE PHONE OBJECT, WITH BOTH OF THE ABOVE ######
test_phone = True

# Play a test file with the dictaphone
fname = "AUDIO_FILES/mortal_kombat.wav"
dic = Dictaphone(audio_dir='AUDIO_FILES')


#### Playback #####
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


signaller = PhoneMonitor(dummy_mode=True)

#### Signaller ####
if test_signalman:
    print("Time to test the signaller")

    print("Starting the signaller. Should start seeing reporting of buttons")
    signaller.start()
    time.sleep(5)

    print("Pressing the button B1")
    signaller.dummy_pressed = 'B1'
    time.sleep(4)

    print("Un-pressing B1")
    signaller.dummy_pressed = None
    time.sleep(4)

    print("The signaller needs to handle functions for the following button:")
    print(signaller.call_button)

    print("Sending signal that the button has been handled")
    signaller.called_button()

    print("The signaller needs to handle functions for the following button:")
    print(signaller.call_button)

    print("Testing the signallers' ability to track button sequence. Pressing the buttons B2, B3, B4...")
    signaller.POLLING_RATE = 0.1
    for i in range(2, 5):
        signaller.dummy_pressed = 'B{}'.format(i)
        time.sleep(0.2)
        signaller.dummy_pressed = None
        time.sleep(0.2)
    print("Reducing verbosity to 3")
    signaller.LOUD = 3
    signaller.POLLING_RATE = 1.0
    print("The signaller recorded the sequence:\n    {}".format(signaller.sequence))
    time.sleep(3)

    print("Sending sequence clear call...")
    signaller.clear_sequence()
    time.sleep(2)
    print("The signaller recorded the sequence:\n    {}".format(signaller.sequence))

    time.sleep(2)

    print("Stopping the signaller. Output should cease")
    signaller.stop()
    time.sleep(5)


#### Phone as a whole ####
if test_phone:
    phone = Phone("AUDIO_FILES")
    print("Starting phone. Should have the monitor begin reporting")
    phone.start()
    time.sleep(5)

    print("Pressing B1 on the monitor")
    phone.monitor.dummy_pressed = 'B1'
    time.sleep(2)
    phone.monitor.dummy_pressed = None
    time.sleep(5)

    phone.stop()

print("Done testing.")

