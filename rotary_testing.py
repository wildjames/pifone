import gpiozero



trigger_pin = 2
counter_pin = 3

def trigger_activated():
    print("Trigger activated!")

trigger_button = gpiozero.Button(trigger_pin, pull_up=False, active_state=False)

print("OK, go!")

trigger_button.when_activated = trigger_activated

print("Trigger initiated!")
