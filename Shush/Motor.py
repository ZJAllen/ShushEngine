__author__ = 'ZJAllen'

from Shush.Board import *
from Shush.Drivers import TMC5160_Registers as Register
import math

class Motor(sBoard):

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

        # Initialize the hardware
        # self.initPeripherals()
        self.defaultSettings()

    def enableMotor(self):
        # Pull all Enable pin LOW (pull HIGH to disable motor)
        gpio.output(self.enablePin, gpio.LOW)

    def disableMotor(self):
        # Pull all Enable pin HIGH
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
        curPos = self.read(Register.XACTUAL)
        print("Current Pos: ", curPos)

        return curPos

    # Move to an absolute position from Home (0) position
    def goTo(self, pos):
        if pos > 0x3fffff: pos = 0x3fffff
        self.write(Register.XTARGET, pos)

    # Read data from the SPI bus
    def read(self, address):
        self.read40bit(address)
        return self.read40bit(address)

    # Write data to the SPI bus
    def write(self, address, data):
        # For write, add 0x80 to address
        address = address | 0x80
        #print('0x{:02x}'.format(address))
        # self.sendData(address, data)

        # Try different method instead of sendData()
        sendBuf = [0] * 5
        print(sendBuf)
        sendBuf[0] = address | 0x80
        sendBuf[1] = 0xFF & (data >> 24)
        sendBuf[2] = 0xFF & (data >> 16)
        sendBuf[3] = 0xFF & (data >> 8)
        sendBuf[4] = 0xFF & data
        print(sendBuf)

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send datagram
        response = sBoard.spi.writebytes(sendBuf)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chipSelect, gpio.HIGH)

    # Send data to the SPI bus
    def sendData(self, address, data):
        # Initialize datagram variable
        datagram = 0

        # Delay 100 us
        time.sleep(0.0001)

        # Delay 10 us before sending data
        time.sleep(0.00001)

        datagram = [(address & 0xFF)]
        datagram.append( (data >> 24) & 0xFF )
        datagram.append( (data >> 16) & 0xFF )
        datagram.append( (data >> 8) & 0xFF )
        datagram.append( data & 0xFF )

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send datagram
        response = sBoard.spi.xfer2(datagram)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chipSelect, gpio.HIGH)

        # return response

    def xfer(self, data):

        # Mask the value to a byte format for transmision
        data = (int(data) & 0xff)

        # Get response back from SPI transfer
        response = sBoard.spi.xfer2([data])

        return response[0]

    def read40bit(self, address):
        addressBuf = [0] * 5
        readBuf = [0] * 5

        # Clear write bit
        addressBuf[0] = address & 0x7F

        readBuf = sBoard.spi.xfer2(addressBuf)

        value = readBuf[1]
        value = value << 8
        value |= readBuf[2]
        value = value << 8
        value |= readBuf[3]
        value = value << 8
        value |= readBuf[4]

        return value
