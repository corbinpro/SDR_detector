____________________________________
# Dependencies:

### Operating System

Tested on: Debian 12 “Bookworm” (64-bit)
Should also work on other Debian-based Linux distributions

Test rtl-sdr with these example command prompts:

    rtl_fm -f 103.3M -M wbfm -s 200k -g 40 -r 48000 - | aplay -r 48000 -f S16_LE

    rtl_fm -f 100.3M -M wbfm -s 200k -g 40 -r 48000 - | aplay -r 48000 -f S16_LE

### System Packages / Libraries

#### These are required to interface with the RTL-SDR hardware and provide core C libraries:

    rtl-sdr           # RTL-SDRUSB drivers & utilities

    librtlsdr-dev     # Development headers for pyrtlsdr

    python3-venv      # To create isolated Python virtual environments

    python3-full      # Ensures full Python installation

    libusb-1.0-0-dev  # USB library required by pyrtlsdr

    rtl_test          # Test RTL-SDR device

    rtl_eeprom        # Read/write RTL-SDR EEPROM

### Python Environment

Python 3.11+ recommended (Python 3.10+ should work)

I used:

    python3 -m venv ~/sdr-venv
    source ~/sdr-venv/bin/activate
    pip install --upgrade pip
    pip install pyrtlsdr numpy

### Hardware:
-RTL-SDR USB dongle (RTL2832U or compatible)
-Antenna tuned for 315 MHz (your car fob frequency)
-USB port with sufficient power

## To run 
venv is necessary(deb12) for python script due to system conflicts.

to open create a venv and run .py program:

    source ~/sdr-venv/bin/activate
then run:

    python rtl_sdr_keyfob_detector.py
to quit venv:

    deactivate

## Also included:
- gnuradio-companion save file for locating target frequencies