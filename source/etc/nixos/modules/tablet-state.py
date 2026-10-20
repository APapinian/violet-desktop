#!/usr/bin/env python3
"""Read only the Yoga tablet switch. Never grabs or reads a keyboard device."""
import json
import fcntl
from contextlib import closing
import os
import time
from pathlib import Path
from evdev import InputDevice, ecodes

TARGET=Path('/run/yoga-tablet/state.json')
NAME='Lenovo Yoga Tablet Mode Control switch'

def publish(tablet, available, error=''):
    temp=TARGET.with_suffix('.tmp')
    temp.write_text(json.dumps(dict(tablet=tablet,available=available,error=error,updated=time.time())))
    temp.chmod(0o644);temp.replace(TARGET)

def main():
    while True:
        try:
            with closing(InputDevice('/dev/input/yoga-tablet-mode')) as device:
                if device.name!=NAME or ecodes.SW_TABLET_MODE not in device.capabilities().get(ecodes.EV_SW,[]):
                    publish(False,False,'Beklenen Yoga SW_TABLET_MODE aygıtı değil');time.sleep(3);continue
                bits=bytearray(8)
                fcntl.ioctl(device.fd, (2<<30)|(len(bits)<<16)|(ord('E')<<8)|0x1b, bits, True)
                publish(bool(bits[ecodes.SW_TABLET_MODE//8] & (1<<(ecodes.SW_TABLET_MODE%8))),True)
                for event in device.read_loop():
                    if event.type==ecodes.EV_SW and event.code==ecodes.SW_TABLET_MODE:publish(bool(event.value),True)
        except OSError:
            publish(False,False,'Tablet anahtarı bekleniyor');time.sleep(2)

if __name__=='__main__':main()
