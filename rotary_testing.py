import gpiozero



trigger_pin = 2
counter_pin = 3

def trigger_activated():
    print("Trigger activated!")

trigger_button = gpiozero.Button(trigger_pin, active_state=True)

print("OK, go!")

trigger_button.wait_for_active()

print("Trigger initiated!")
