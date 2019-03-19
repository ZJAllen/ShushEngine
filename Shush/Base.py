#!/usr/bin/python3

# Shush system includes
import time
import os
import sys

import spidev as spidev
import RPi.GPIO as gpio

gpio.setwarnings(False)

'''
# Include the spidev module and check if SPI is enabled
try:
  import spidev as spidev
except ImportError:
  raise ImportError("Cannot load spidev library")

# Include the GPIO module
  try:
    import RPi.GPIO as gpio
  except ImportError:
    raise ImportError("Cannot load the Raspberry Pi GPIO drivers")
'''
