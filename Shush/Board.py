__author__ = 'ZJAllen'

import Shush.Boards.SlushEngine_MKI as SL1
from Slush.Base import *

# Need to update everything
class sBoard:
  chip = 0
  bus = 0

  def __init__(self):
    # Initialize the peripherals (SPI and GPIO)
    self.initSPI()
    self.initGPIOState()
    # self.initI2C()  # No I2C devices yet

  def initGPIOState(self):
    # Sets the default states for the GPIO on the Shush modules.
    # Only applies to Raspberry Pi

    gpio.setmode(gpio.BCM)

    # Common motor reset pin (needs to be set up)
    # gpio.setup(SL1.L6470_Reset, gpio.OUT)

    # Define chip select pins
    gpio.setup(SL1.M0_CS, gpio.OUT)
    gpio.setup(SL1.M1_CS, gpio.OUT)
    gpio.setup(SL1.M2_CS, gpio.OUT)
    gpio.setup(SL1.M3_CS, gpio.OUT)
    gpio.setup(SL1.M4_CS, gpio.OUT)
    gpio.setup(SL1.M5_CS, gpio.OUT)

    # Pull all CS pins HIGH (LOW initializes data transmission)
    gpio.output(SL1.M0_CS, gpio.HIGH)
    gpio.output(SL1.M1_CS, gpio.HIGH)
    gpio.output(SL1.M2_CS, gpio.HIGH)
    gpio.output(SL1.M3_CS, gpio.HIGH)
    gpio.output(SL1.M4_CS, gpio.HIGH)
    gpio.output(SL1.M5_CS, gpio.HIGH)

    #IO expander reset pin (does not yet exist)
    # gpio.setup(SL1.MCP23_Reset, gpio.OUT)
    # gpio.output(SL1.MCP23_Reset, gpio.HIGH)

    resetDrivers()

  def resetDrivers(self):
    # Reset all drivers
    '''  NEEDS TO BE SET UP

    gpio.output(SL1.TMC5160_Reset, gpio.LOW)
    time.sleep(.01)
    gpio.output(SL1.TMC5160_Reset, gpio.HIGH)
    time.sleep(.01)

    '''

  def initSPI(self):
    # Initialize SPI Bus for motor drivers
    sBoard.spi = spidev.SpiDev()
    sBoard.spi.open(0,0)                # Open(Bus, Device)
    sBoard.spi.max_speed_hz = 1000000   # 1 MHZ
    sBoard.spi.bits_per_word = 32       # 32 bits per word
    sBoard.spi.loop = False
    sBoard.spi.mode = 3                 # SPI Mode 3

  def deinitBoard(self):
    # Closes the board and releases the peripherals
    gpio.cleanup()
