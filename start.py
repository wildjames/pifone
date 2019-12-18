#!/usr/bin/python3
from subprocess import Popen

filename = 'pifone.py'
while True:
    print("\nStarting " + filename)
    p = Popen("python3 " + filename, shell=True)
    p.wait()