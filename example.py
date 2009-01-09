#! /usr/bin/env python

"""pyduino - A python library to interface with the firmata arduino firmware.
Copyright (C) 2007 Joe Turner <orphansandoligarchs@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import pyduino
import sys
import time

def usage():
    print """Usage: ./example.py port mode pin
Available modes: 1 - Digital input
                 2 - Digital output
                 3 - PWM
                 4 - Analog input"""

if __name__ == "__main__":
    try:
        arduino = pyduino.Arduino(sys.argv[1])
        mode = int(sys.argv[2])
        pin = int(sys.argv[3])
    except IndexError, ValueError:
        usage()
        sys.exit()
    if mode == 1:
        #Digital input
        arduino.digital[pin].set_active(1)
        arduino.digital[pin].set_mode(pyduino.DIGITAL_INPUT)
    if mode == 2:
        #Digital output
        arduino.digital[pin].set_active(1)
        arduino.digital[pin].set_mode(pyduino.DIGITAL_OUTPUT)
        arduino.digital[pin].write(1)    #Turn output high
    if mode == 3:
        #Digital PWM
        arduino.digital[pin].set_active(1)
        arduino.digital[pin].set_mode(pyduino.DIGITAL_PWM)
    if mode == 4:
        #Analog in
        arduino.analog[pin].set_active(1)
    
    last_value = 0
    #Mainloop
    while 1:
        try: 
            arduino.iterate()
            if mode == 1:
                #Digital input
                value = arduino.digital[pin].read()
                if value != last_value:
                    last_value = value
                    if value == 1: 
                        print "Digital pin is high"
                    else:
                        print "Digital pin is low"
            if mode == 2:
                #Digital output
                #Alter the value every second
                value = int(time.time() % 2)
                arduino.digital[pin].write(value)
            if mode == 3:
                #Digital PWM
                #Alter the value every second
                value = int(time.time() % 32) * 8
                arduino.digital[pin].write(value)
            if mode == 4:
                #Analog in
                value = arduino.analog[pin].read()
                if value != last_value:
                    last_value = value
                    print "Analog pin value is %i"% value
        except KeyboardInterrupt:
            arduino.exit()
            break

