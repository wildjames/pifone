#!/usr/bin/python3
from subprocess import Popen
import os

mydir = os.path.dirname(__file__)
os.chdir(mydir)

filename = '/home/pi/pifone/pifone.py'
while True:
    print("\nStarting " + filename)

    p = Popen("python3 " + filename, shell=True)
    p.wait()
