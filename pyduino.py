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

__version__ = "0.1"

import serial

# Message command bytes - straight outta Pd_firmware.pde
DIGITAL_MESSAGE = 0x90 # send data for a digital pin
ANALOG_MESSAGE = 0xE0 # send data for an analog pin (or PWM)

# PULSE_MESSAGE = 0xA0 # proposed pulseIn/Out message (SysEx)
# SHIFTOUT_MESSAGE = 0xB0 # proposed shiftOut message (SysEx)

REPORT_ANALOG_PIN = 0xC0 # enable analog input by pin #
REPORT_DIGITAL_PORTS = 0xD0 # enable digital input by port pair
START_SYSEX = 0xF0 # start a MIDI SysEx message
SET_DIGITAL_PIN_MODE = 0xF4 # set a digital pin to INPUT or OUTPUT
END_SYSEX = 0xF7 # end a MIDI SysEx message
REPORT_VERSION = 0xF9 # report firmware version
SYSTEM_RESET = 0xFF # reset from MIDI

# Pin modes
DIGITAL_INPUT = 0
DIGITAL_OUTPUT = 1
DIGITAL_PWM = 2

PWM_PINS = (9, 10, 11)

class Arduino:
    """Base class for the arduino board"""

    def __init__(self, port):
        self.sp = serial.Serial(port, 57600, timeout=0.02)
        self.digital = []
        for i in range(14):
            self.digital.append(Digital(self.sp, i))

        self.analog = []
        for i in range(6):
            self.analog.append(Analog(self.sp, i))

        #Obtain firmata version
        self.sp.write(chr(REPORT_VERSION))

    def __str__(self):
        return "Arduino: %s"% self.sp.port
            
    def iterate(self):
        """Read and handle a command byte from Arduino's serial port"""
        data = self.sp.read()
        if data != "":
            self._process_input(ord(data))

    def _process_input(self, data):
        """Process a command byte and any additional information bytes"""
        if data < 0xF0:
            #Multibyte
            message = data & 0xF0
            pin = data & 0x0F
            if message == DIGITAL_MESSAGE:
                #Digital in
                lsb = ""
                msb = ""
                while lsb == "":
                    lsb = self.sp.read()
                while msb == "":
                    msb = self.sp.read()
                lsb = ord(lsb)
                msb = ord(msb)
                Digital.mask = lsb + (msb << 7)
            elif message == ANALOG_MESSAGE:
                #Analog in
                lsb = ""
                msb = ""
                while lsb == "":
                    lsb = self.sp.read()
                while msb == "":
                    msb = self.sp.read()
                lsb = ord(lsb)
                msb = ord(msb)
                self.analog[pin].value = msb << 7 | lsb
        elif data == REPORT_VERSION:
            major, minor = self.sp.read(2)
            self.firmata_version = (ord(major), ord(minor))

    def get_firmata_version(self):
        """Return a (major, minor) version tuple for the firmata firmware"""
        return self.firmata_version

    def exit(self):
        """Exit the application cleanly"""
        self.sp.close()


class Digital:
    """Digital pin on the arduino board"""

    mask = 0

    def __init__(self, sp, pin):
        self.sp = sp
        self.pin = pin
        self.is_active = 0
        self.value = 0
        self.mode = DIGITAL_INPUT

    def __str__(self):
        return "Digital Port %i"% self.pin

    def set_active(self, active):
        """Set the pin to report values"""
        self.is_active = 1
        pin = REPORT_DIGITAL_PORTS + self.pin 
        self.sp.write(chr(pin) + chr(active))

    def get_active(self):
        """Return whether the pin is reporting values"""
        return self.is_active

    def set_mode(self, mode):
        """Set the mode of operation for the pin
        
        Argument:
        mode, takes a value of: - DIGITAL_INPUT
                                - DIGITAL_OUTPUT 
                                - DIGITAL_PWM

        """
        if mode == DIGITAL_PWM and self.pin not in PWM_PINS:
            error_message = "Digital pin %i does not have PWM capabilities" \
                            % (self.pin)
            raise IOError, error_message
        if self.pin < 2:
            raise IOError, "Cannot set mode for Rx/Tx pins" 
        self.mode = mode
        command = chr(SET_DIGITAL_PIN_MODE) + chr(self.pin) + chr(mode)
        self.sp.write(command)

    def get_mode(self):
        """Return the pin mode, values explained in set_mode()"""
        return self.mode

    def read(self):
        """Return the output value of the pin, values explained in write()"""
        if self.mode == DIGITAL_PWM:
            return self.value
        else:
            return (self.__class__.mask & 1 << self.pin) > 0

    def write(self, value):
        """Output a voltage from the pin

        Argument:
        value, takes a boolean if the pin is in output mode, or a value from 0
        to 255 if the pin is in PWM mode

        """
        if self.mode == DIGITAL_INPUT:
            error_message = "Digital pin %i is not an output"% self.pin
            raise IOError, error_message
        elif value != self.read():
            if self.mode == DIGITAL_OUTPUT:
                #Shorter variable dammit!
                mask = self.__class__.mask
                mask ^= 1 << self.pin
                message = chr(DIGITAL_MESSAGE) + chr(mask % 128) \
                          + chr(mask >> 7)
                self.sp.write(message)
                #Set the attribute to the new mask
                self.__class__.mask = mask
            elif self.mode == DIGITAL_PWM:
                self.value = value
                pin = ANALOG_MESSAGE + self.pin
                self.sp.write(chr(pin) + chr(value % 128) + chr(value >> 7))


class Analog:
    """Analog pin on the arduino board"""

    def __init__(self, sp, pin):
        self.sp = sp
        self.pin = pin
        self.active = 0
        self.value = 0

    def __str__(self):
        return "Analog Input %i"% self.pin

    def set_active(self, active):
        """Set the pin to report values"""
        self.active = active
        pin = REPORT_ANALOG_PIN + self.pin
        self.sp.write(chr(pin) + chr(active))

    def get_active(self):
        """Return whether the pin is reporting values"""
        return self.active

    def read(self):
        """Return the input in the range 0-1024"""
        return self.value

