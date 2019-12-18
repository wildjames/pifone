#!/usr/bin/python
from subprocess import Popen

filename = 'pifone.py'
while True:
    print("\nStarting " + filename)
    p = Popen("python " + filename, shell=True)
    p.wait()