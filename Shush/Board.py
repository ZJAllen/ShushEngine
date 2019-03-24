__author__ = 'ZJAllen'

import Shush.Boards.ShushEngine_MKI as SL1
from Shush.Base import *

class Board:
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

    # Define chip select pins
    gpio.setup(SL1.M0_CS, gpio.OUT)
    gpio.setup(SL1.M1_CS, gpio.OUT)
    gpio.setup(SL1.M2_CS, gpio.OUT)
    gpio.setup(SL1.M3_CS, gpio.OUT)
    gpio.setup(SL1.M4_CS, gpio.OUT)
    gpio.setup(SL1.M5_CS, gpio.OUT)

    # Define enable pins
    gpio.setup(SL1.M0_Enable, gpio.OUT)
    gpio.setup(SL1.M1_Enable, gpio.OUT)
    gpio.setup(SL1.M2_Enable, gpio.OUT)
    gpio.setup(SL1.M3_Enable, gpio.OUT)
    gpio.setup(SL1.M4_Enable, gpio.OUT)
    gpio.setup(SL1.M5_Enable, gpio.OUT)

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

  def initSPI(self):
    # Initialize SPI Bus for motor drivers
    Board.spi = spidev.SpiDev()
    Board.spi.open(0,0)               # Open(Bus, Device)
    Board.spi.max_speed_hz = 1000000  # 1 MHZ
    Board.spi.bits_per_word = 8       # 8 bits per word (32-bit word is broken into 4x 8-bit words)
    Board.spi.loop = False
    Board.spi.mode = 3                # SPI Mode 3

  def deinitBoard(self):
    # Closes the board and releases the peripherals
    gpio.cleanup()
