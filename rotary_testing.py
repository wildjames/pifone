import gpiozero



trigger_pin = 2
counter_pin = 3


trigger_button = gpiozero.Button(trigger_pin)
trigger_button.wait_for_active()

print("Trigger initiated!")
