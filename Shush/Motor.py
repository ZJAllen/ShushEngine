__author__ = 'ZJAllen'

from Shush.Board import *
from Shush.Drivers import TMC5160_Registers as Register
import math

class Motor(Board):

    boardInUse = 0

    def __init__(self, motor):

        # Setting the CS pin according to the motor called
        if motor == 0:
            self.chipSelect = SL1.M0_CS
            self.enablePin = SL1.M0_Enable
        if motor == 1:
            self.chipSelect = SL1.M1_CS
            self.enablePin = SL1.M1_Enable
        if motor == 2:
            self.chipSelect = SL1.M2_CS
            self.enablePin = SL1.M2_Enable
        if motor == 3:
            self.chipSelect = SL1.M3_CS
            self.enablePin = SL1.M3_Enable
        if motor == 4:
            self.chipSelect = SL1.M4_CS
            self.enablePin = SL1.M4_Enable
        if motor == 5:
            self.chipSelect = SL1.M5_CS
            self.enablePin = SL1.M5_Enable

        # Initially set to default settings.  These can be changed and configured at any time.
        self.defaultSettings()

    def enableMotor(self):
        # Pull Enable pin LOW (pull HIGH to disable motor)
        gpio.output(self.enablePin, gpio.LOW)

    def disableMotor(self):
        # Pull Enable pin HIGH
        gpio.output(self.enablePin, gpio.HIGH)

    # Set default motor parameters
    def defaultSettings(self):
        # MULTISTEP_FILT = 1, EN_PWM_MODE = 1 enables stealthChop
        self.write(Register.GCONF, 0x0000000C)

        # TOFF = 3, HSTRT = 4, HEND = 1, TBL = 2, CHM = 0 (spreadCycle)
        self.write(Register.CHOPCONF, 0x000100C3)

        # IHOLD = 8, IRUN = 15 (max current), IHOLDDELAY = 6
        self.write(Register.IHOLD_IRUN, 0x00080F0A)

        # TPOWERDOWN = 10: Delay before powerdown in standstill
        self.write(Register.TPOWERDOWN, 0x0000000A)

        #TPWMTHRS = 500
        self.write(Register.TPWMTHRS, 0x000001F4)

        self.write(Register.VSTART, 1)
        self.write(Register.A1, 50000)
        self.write(Register.V1, 50000)
        self.write(Register.AMAX, 500000)
        self.write(Register.VMAX, 5000000)
        self.write(Register.DMAX, 50000)
        self.write(Register.D1, 5000)
        self.write(Register.VSTOP, 10)

        self.write(Register.RAMPMODE, 0)
        self.write(Register.XACTUAL, 0)
        self.write(Register.XTARGET, 0)

    # TODO: add some more functionality...

    # Get the posistion of the motor
    def getPos(self):
        currentPos = self.read(Register.XACTUAL)
        print("Current Pos: ", currentPos)

        return currentPos

    # Move to an absolute position from Home (0) position
    def goTo(self, pos):
        # Position range is from -2^31 to +(2^31)-1
        maxPos = (2 *31) - 1
        minPos = -(2**31)

        # Check if position is within bounds
        if pos > maxPos:
            pos = maxPos
            print("Maximum position reached! Stopped at max value.")
        elif pos < minPos:
            pos = minPos
            print("Minimum position reached! Stopped at min value.")

        self.write(Register.XTARGET, pos)

    def calibrateHome(self, direction):
        '''
        Take direction as left or right, drive that direction until limit is hit,
        latch with XLATCH register, etc.  Ref. TMC5160 datasheet for procedure
        '''

    # Read data from the SPI bus
    def read(self, address):
        addressBuf = [0] * 5
        readBuf = [0] * 5

        # Clear write bit
        addressBuf[0] = address & 0x7F

        readBuf = sendData(addressBuf)

        # Parse data returned from SPI transfer/read
        value = readBuf[1]
        value = value << 8
        value |= readBuf[2]
        value = value << 8
        value |= readBuf[3]
        value = value << 8
        value |= readBuf[4]

        return value

    # Write data to the SPI bus
    def write(self, address, data):
        writeBuf = [0] * 5

        # For write access, add 0x80 to address
        writeBuf[0] = address | 0x80

        writeBuf[1] = 0xFF & (data >> 24)
        writeBuf[2] = 0xFF & (data >> 16)
        writeBuf[3] = 0xFF & (data >> 8)
        writeBuf[4] = 0xFF & data

        sendData(writeBuf)

    def sendData(self, dataArray):

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send data
        response = sBoard.spi.xfer2(dataArray)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chipSelect, gpio.HIGH)

        return response
