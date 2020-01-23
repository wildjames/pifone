# pifone
A raspberry pi-based dictaphone


This project is one of those that I'll never fully finish, I suspect. Starting from scratch so I don't inherit my crappy logic from before, when I was learining a lot about GPIO, audio streams, and classes.

I'm sorry for the atrocities I'm about to commit

# SETTING UP A NEW rPI

### Hardware Nonsense

You'll need to connect up the correct pins to the relevant contacts. 
  - Dial pad / rotator
  - Handset switch
  - Indicator LED

Then bolt on the USB hat, and plug in the sound card & female port. Then, arrange inside the casing and glue down!
  
### Software will need loading onto the Pi

We need to grab a load of python gubbins
```
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python-pyaudio python3-pip python3-numpy libatlas-base-dev
git clone https://github.com/wildjames/pifone
cd pifone
sudo -H pip3 install -r requirements.txt
```
This installs the modules as root, for the service later. Then:

### Disable the built-in sound card for the pi

[from here](https://superuser.com/questions/989385/how-to-make-raspberry-pi-use-an-external-usb-sound-card-as-a-default)

If you don't need the onboard audio chip (i.e. analog output or hdmi audio), disable it and then the USB audio device can become the primary device:

  - Disable onboard audio.
    - Open /etc/modprobe.d/raspi-blacklist.conf and add blacklist snd_bcm2835.
    - Allow the USB audio device to be the default device.
    - Open /lib/modprobe.d/aliases.conf and comment out the line options snd-usb-audio index=-2
  - Reboot
    - sudo reboot
  - Test it out.
    - `$aplay /usr/share/sounds/alsa/Front_Center.wav`


### Add the `start.py` script to the boot services

`sudo nano /lib/systemd/system/pifone.service` and add this to it:

```
[Unit]
Description=PiFone
After=multi-user.target

[Service]
Type=idle
ExecStart=/home/pi/pifone/start.py
RootDirectory=/home/pi/pifone/
WorkingDirectory=/home/pi/pifone/
User=pi

[Install]
WantedBy=multi-user.target
```

Then:
```
sudo chmod 644 /lib/systemd/system/pifone.service
sudo systemctl daemon-reload
sudo systemctl enable pifone.service
```
    
    
TODO: Create a disk image I can burn that already has all this done.
