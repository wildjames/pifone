import gpiozero
from time import sleep


trigger_pin = 17
counter_pin = 27


N_PULSES = 0
def trigger_activated():
    print("Trigger activated!")

    global N_PULSES
    N_PULSES = 0

def add_pulse():
    global N_PULSES
    N_PULSES += 1
    print("SAW A PULSE: Now at {}".format(N_PULSES))

def report_pulse_number():
    print("The pulse pin say {} pulses".format(N_PULSES))

trigger_button = gpiozero.Button(trigger_pin, pull_up=False)
pulse_button = gpiozero.Button(counter_pin, pull_up=False)

pulse_button.when_deactivated = add_pulse

trigger_button.when_activated = trigger_activated
trigger_button.when_deactivated = report_pulse_number

print("OK, go!")
sleep(60)
