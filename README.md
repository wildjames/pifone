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
  
### Disk image

Flash the latest raspbian image. Then `touch /Volumes/boot/ssh`. After that, enable USB gadget mode by adding 
  
### Software will need loading onto the Pi

We need to grab a load of python gubbins
```
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python-pyaudio python3-pip python3-numpy libatlas-base-dev alsa-utils
git clone https://github.com/wildjames/pifone
cd pifone
sudo -H pip3 install -r requirements.txt
```
This installs the modules as root, for the service later. Then:

### Disable the built-in sound card for the pi

[from here](https://www.instructables.com/id/Disable-the-Built-in-Sound-Card-of-Raspberry-Pi/)

Create a blacklist file and add the soundcard to it:
```
echo "blacklist snd_bcm2835" >> alsa-blacklist.conf
sudo mv alsa-blacklist.conf /etc/modprobe.d/
```

#### If on a zero W

you can ssh in over wifi, and connect while the dongle is in. At this point, test that the pifone works by just running `start.py` in the pifone directory, as the user `pi`.

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
