# pifone
A raspberry pi-based dictaphone


This project is one of those that I'll never fully finish, I suspect. Starting from scratch so I don't inherit my crappy logic from before, when I was learining a lot about GPIO, audio streams, and classes.

I'm sorry for the atrocities I'm about to commit

# SETTING UP A NEW rPI

You'll need to connect up the correct pins to the relevant contacts. 
  - Dial pad / rotator
  - Handset switch
  - Indicator LED
Then bolt on the USB hat, and plug in the sound card & female port. Then, arrange inside the casing and glue down!
  
Software will need loading onto the Pi;
  - `sudo apt-get update && sudo apt-get upgrade -y`
  - `sudo apt-get install -y git python-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python-pyaudio python3-pip python3-numpy libatlas-base-dev`
  - `git clone https://github.com/wildjames/pifone`
  - `cd pifone`
  - `pip3 install -r requirements.txt`
  - Disable the built-in sound card for the pi
  - Add the start script to the boot `/etc/rc.local`
    - `/home/pi/pifone/start.py > null`
    
    
TODO: Create a disk image I can burn that already has all this done.
