import time
from listener import Dictaphone, ButtonMonitor, Phone
import os


###### TEST THE DICTAPHONE OBJECT ######
test_playback = True
test_recording = False

###### TEST THE SIGNAL SENDER AND RECIEVER ######
test_signalman = False

###### TEST THE PHONE OBJECT, WITH BOTH OF THE ABOVE ######
test_phone = False

if test_playback or test_recording:
    fname = "AUDIO_FILES/mortal_kombat.wav"
    dic = Dictaphone(audio_dir='AUDIO_FILES')

if test_signalman:
    signaller = ButtonMonitor(dummy_mode=True)


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



#### Signaller ####
if test_signalman:
    print("THIS IS ALL OUTDATED AND NO LONGER TESTS ANYTHING!!!")
    print("Time to test the signaller")

    print("Pressing the button 1")
    signaller.mock_pins[1].drive_low()
    time.sleep(0.1)

    print("Un-pressing 1")
    signaller.mock_pins[1].drive_high()
    time.sleep(2)

    print("The signaller needs to handle functions for the following button:")
    print(signaller.call_button)

    print("\n\nRepeating the above, but lifting the handset first")
    signaller.mock_pins[22].drive_low()
    time.sleep(2)
    print("Pressing the button 1")
    signaller.mock_pins[1].drive_low()
    time.sleep(0.5)
    print("Un-pressing 1")
    signaller.mock_pins[1].drive_high()
    time.sleep(5)

    print("The signaller needs to handle functions for the following button:")
    print(signaller.call_button)

    print("Sending signal that the button has been handled")
    signaller.called_button()

    print("The signaller needs to handle functions for the following button:")
    print(signaller.call_button)

    print("Testing the signallers' ability to track button sequence. Pressing the buttons B2, B3, B4...")
    for i in range(2, 11):
        signaller.mock_pins[i].drive_low()
        time.sleep(0.1)
        signaller.mock_pins[i].drive_high()
        time.sleep(0.1)

    print("The signaller wants us to parse the function for button {}".format(signaller.call_button))

    print("Reducing verbosity to 3")
    signaller.LOUD = 3
    signaller.POLLING_RATE = 1.0
    print("The signaller recorded the sequence:\n    {}".format(signaller.sequence))
    time.sleep(3)

    print("Sending handset down")
    signaller.mock_pins[0].drive_high()
    time.sleep(2)
    print("The signaller recorded the sequence:\n    {}".format(signaller.sequence))

    time.sleep(2)
    print("Done testing signaller")



#### Phone as a whole ####
if test_phone:
    phone = Phone("AUDIO_FILES")
    print("\n\n\nStarting phone. Should have the monitor begin reporting")
    phone.start()
    time.sleep(3)

    print("Pressing B2 on the monitor")
    phone.monitor.mock_pins[2].drive_low()
    time.sleep(2)
    print("Releasing B2 on the monitor")
    phone.monitor.mock_pins[2].drive_high()
    time.sleep(5)

    print("Lifting handset")
    phone.monitor.mock_pins[0].drive_low()
    time.sleep(2)

    print("Pressing B2 on the monitor")
    phone.monitor.mock_pins[2].drive_low()
    time.sleep(2)
    phone.monitor.mock_pins[2].drive_high()
    time.sleep(5)

    print("Replacing handset")
    phone.monitor.mock_pins[0].drive_high()
    time.sleep(5)

    phone.stop()

print("Done testing.")

