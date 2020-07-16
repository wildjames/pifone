# pifone
A raspberry pi-based dictaphone, housed in old-timey phones. I originally made this for my wedding, for people to leave cute recordings on. When that was over though, there were still some rough edges I wanted to smooth out, plus I wanted to try it with a rotary phone. As it stands, I've build four of these, of varying quality. 

This project is one of those that I'll never fully finish, I suspect. Starting from scratch so I don't inherit my crappy logic from before, when I was learining a lot about GPIO, audio streams, and classes.

I'm sorry for the atrocities I'm about to commit

# SETTING UP A NEW rPI

### Hardware Nonsense

You'll need to connect up the correct pins to the relevant contacts. 
  - Dial pad / rotator
  - Handset switch
  - Indicator LED

This will be highly dependant on the physical phone that you're using, so I want to avoid setting hard requirements on this. You'll very likely have to alter the ButtonMonitor class!

Then bolt on the USB hat, and plug in the sound card & female port. Then, arrange inside the casing and glue down!
  
### Disk image

Flash the latest raspbian image. Then `touch /Volumes/boot/ssh`. After that, enable USB gadget mode by adding 
  
### Software will need loading onto the Pi

We need to grab a load of python gubbins
```
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python3-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python3-pyaudio python3-pip python3-numpy libatlas-base-dev alsa-utils
git clone https://github.com/wildjames/pifone
cd pifone
sudo -H pip3 install -r requirements.txt
```
This installs the modules as root, for the service later. Then:

### Disable the built-in sound card for the pi

[from here](https://www.instructables.com/id/Disable-the-Built-in-Sound-Card-of-Raspberry-Pi/)

The USB sound device can be made the default audio device by editing a system file “alsa.conf” :

```
sudo nano /usr/share/alsa/alsa.conf
```
Scroll and find the following two lines:
```
defaults.ctl.card 0
defaults.pcm.card 0
```

Change the 0 to a 1 to match the card number of the USB device :

```
defaults.ctl.card 1
defaults.pcm.card 1
```

#### If on a zero W

you can ssh in over wifi, and connect while the dongle is in. At this point, test that the pifone works by just running `start.py` in the pifone directory, as the user `pi`. Alternatively:

```
aplay /usr/share/sounds/alsa/Front_Center.wav
```

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

For some reason, this sometimes crashes for me on some installations and not others. I'm too lazy to figure out why, so an alternative is to add it to the crontab:

```
crontab -e
```
and add this line:
```
@reboot /home/pi/pifone/start.py
```
which seems to do the trick.

## TODOs:
  - Create a disk image I can burn that already has all this done.
  - Put in some pictures
  - Write a base ButtonMonitor class, that gets built on top of for each phone I make.
