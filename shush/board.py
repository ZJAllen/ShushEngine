__author__ = 'ZJAllen'

import shush.boards.shush_mk1 as s1

import spidev as spidev
import RPi.GPIO as gpio

gpio.setwarnings(False)


class Board:

    def __init__(self):
        # Initialize the peripherals (SPI and GPIO)
        self.init_spi()
        self.init_gpio_state()

    def init_gpio_state(self):
        # Sets the default states for the GPIO on the Shush modules.
        # Only applies to Raspberry Pi

        gpio.setmode(gpio.BCM)

        # Define chip select pins
        gpio.setup(s1.m0_cs, gpio.OUT)
        gpio.setup(s1.m1_cs, gpio.OUT)
        gpio.setup(s1.m2_cs, gpio.OUT)
        gpio.setup(s1.m3_cs, gpio.OUT)
        gpio.setup(s1.m4_cs, gpio.OUT)
        gpio.setup(s1.m5_cs, gpio.OUT)

        # Define enable pins
        gpio.setup(s1.m0_enable, gpio.OUT)
        gpio.setup(s1.m1_enable, gpio.OUT)
        gpio.setup(s1.m2_enable, gpio.OUT)
        gpio.setup(s1.m3_enable, gpio.OUT)
        gpio.setup(s1.m4_enable, gpio.OUT)
        gpio.setup(s1.m5_enable, gpio.OUT)

        # Pull all cs pins HIGH (LOW initializes data transmission)
        gpio.output(s1.m0_cs, gpio.HIGH)
        gpio.output(s1.m1_cs, gpio.HIGH)
        gpio.output(s1.m2_cs, gpio.HIGH)
        gpio.output(s1.m3_cs, gpio.HIGH)
        gpio.output(s1.m4_cs, gpio.HIGH)
        gpio.output(s1.m5_cs, gpio.HIGH)

    def init_spi(self):
        # Initialize SPI Bus for motor drivers.

        Board.spi = spidev.SpiDev()

        # Open(Bus, Device)
        Board.spi.open(0, 0)

        # 1 MHZ
        Board.spi.max_speed_hz = 1000000

        # 8 bits per word (32-bit word is broken into 4x 8-bit words)
        Board.spi.bits_per_word = 8

        Board.spi.loop = False

        # SPI Mode 3
        Board.spi.mode = 3

    def deinitBoard(self):
        # Closes the board and releases the peripherals.
        gpio.cleanup()
