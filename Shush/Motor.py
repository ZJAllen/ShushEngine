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


    ''' Need to update all this stuff
    # initalise the appropriate pins and buses
    def initPeripherals(self):

        #check that the motors SPI is actually working
        if (self.getParam(LReg.CONFIG) == 0x2e88):
            print ("Motor Drive Connected on GPIO " + str(self.chipSelect))
            self.boardInUse = 0
        elif (self.getParam([0x1A, 16]) == 0x2c88):
            print ("High Power Drive Connected on GPIO " + str(self.chipSelect))
            self.boardInUse = 1
        else:
            print ("communication issues; check SPI configuration and cables")

        #based on board type init driver accordingly
        if self.boardInUse == 0:
            self.setOverCurrent(2000)
            self.setMicroSteps(16)
            self.setCurrent(70, 90, 100, 100)
            self.setParam([0x1A, 16], 0x3608)
        if self.boardInUse == 1:
            self.setParam([0x1A, 16], 0x3608)
            self.setCurrent(100, 120, 140, 140)
            self.setMicroSteps(16)

        #self.setParam(LReg.KVAL_RUN, 0xff)
        self.getStatus()
        self.free()

    # check if the motion engine is busy
    def isBusy(self):
        status = self.getStatus()
        return (not ((status >> 1) & 0b1))

    # wait for motor to finish moving *** Caution this is blocking ***
    def waitMoveFinish(self):
        status = 1
        while status:
            status = self.getStatus()
            status = not((status >> 1) & 0b1)

    # set the microstepping level
    def setMicroSteps(self, microSteps):
        self.free()
        stepVal = 0

        for stepVal in range(0, 8):
            if microSteps == 1:
                break
            microSteps = microSteps >> 1;

        self.setParam(LReg.STEP_MODE, (0x00 | stepVal | LReg.SYNC_SEL_1))

    # set the threshold speed of the motor
    def setThresholdSpeed(self, thresholdSpeed):
        if thresholdSpeed == 0:
            self.setParam(LReg.FS_SPD, 0x3ff)
        else:
            self.setParam(LReg.FS_SPD, self.fsCalc(thresholdSpeed))

    # set the current
    def setCurrent(self, hold, run, acc, dec):
        self.setParam(LReg.KVAL_RUN, run)
        self.setParam(LReg.KVAL_ACC, acc)
        self.setParam(LReg.KVAL_DEC, dec)
        self.setParam(LReg.KVAL_HOLD, hold)

    # set the maximum motor speed
    def setMaxSpeed(self, speed):
        self.setParam(LReg.MAX_SPEED, self.maxSpdCalc(speed))

    # set the minimum speed
    def setMinSpeed(self, speed):
        self.setParam(LReg.MIN_SPEED, self.minSpdCalc(speed))

    # set accerleration rate
    def setAccel(self, acceleration):
        accelerationBytes = self.accCalc(acceleration)
        self.setParam(LReg.ACC, accelerationBytes)

    # set the deceleration rate
    def setDecel(self, deceleration):
        decelerationBytes = self.decCalc(deceleration)
        self.setParam(LReg.DEC, decelerationBytes)



    # get the speed of the motor
    def getSpeed(self):
        return self.getParam(LReg.SPEED)

    # set the overcurrent threshold
    def setOverCurrent(self, ma_current):
        OCValue = math.floor(ma_current/375)
        if OCValue > 0x0f: OCValue = 0x0f
        self.setParam((LReg.OCD_TH), OCValue)

    # set the stall current level
    def setStallCurrent(self, ma_current):
        STHValue = round(math.floor(ma_current/31.25))
        if(STHValue > 0x80): STHValue = 0x80
        if(STHValue < 0): STHValue = 9
        self.setParam((LReg.STALL_TH), STHValue)

    # set low speed optamization
    def setLowSpeedOpt(self, enable):
        self.xfer(LReg.SET_PARAM | LReg.MIN_SPEED[0])
        if enable: self.param(0x1000, 13)
        else: self.param(0, 13)

    # start the motor spinning
    def run(self, dir, spd):
        speedVal = self.spdCalc(spd)
        self.xfer(LReg.RUN | dir)
        if speedVal > 0xfffff: speedVal = 0xfffff
        self.xfer(speedVal >> 16)
        self.xfer(speedVal >> 8)
        self.xfer(speedVal)

    # sets the clock source
    def stepClock(self, dir):
        self.xfer(LReg.STEP_CLOCK | dir)

    # move the motor a number of steps
    def move(self, nStep):
        dir = 0

        if nStep >= 0:
            dir = LReg.FWD
        else:
            dir = LReg.REV

        n_stepABS = abs(nStep)

        self.xfer(LReg.MOVE | dir)
        if n_stepABS > 0x3fffff: nStep = 0x3fffff
        self.xfer(n_stepABS >> 16)
        self.xfer(n_stepABS >> 8)
        self.xfer(n_stepABS)


    '''
    # Get the posistion of the motor
    def getPos(self):
        curPos = self.read(Register.XACTUAL)
        print("Current Pos: ", curPos)

        return curPos

    # Move to an absolute position from Home (0) position
    def goTo(self, pos):
        if pos > 0x3fffff: pos = 0x3fffff
        self.write(Register.XTARGET, pos)

    # TODO: add some more functionality...

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
        sendBuf = [None] * 5
        sendBuf[0] = address | 0x80
        sendBuf[1] = 0xFF & (data >> 24)
        sendBuf[2] = 0xFF & (data >> 16)
        sendBuf[3] = 0xFF & (data >> 8)
        sendBuf[4] = 0xFF & data

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send datagram
        response = sBoard.spi.writebytes(datagram)

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
        # Clear write bit
        addressBuf = [None] * 5
        readBuf = [None] * 5
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
