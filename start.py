#!/usr/bin/python3
from subprocess import Popen

filename = 'pifone.py'
while True:
    print("\nStarting " + filename)
    try:
        p = Popen("python3 " + filename, shell=True)
        p.wait()
    except SystemExit:
        break