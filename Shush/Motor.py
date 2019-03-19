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
            print("Chip Select: ", self.chipSelect)
        if motor == 1:
            self.chipSelect = SL1.M1_CS
        if motor == 2:
            self.chipSelect = SL1.M2_CS
        if motor == 3:
            self.chipSelect = SL1.M3_CS
        if motor == 4:
            self.chipSelect = SL1.M4_CS
        if motor == 5:
            self.chipSelect = SL1.M5_CS

        # Initialize the hardware
        # self.initPeripherals()
        self.defaultSettings()

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
        curPos = self.read(Register.XACTUAL, 0)
        print("Current Pos: ", curPos)
        return curPos

    # Move to an absolute position from Home (0) position
    def goTo(self, pos):
        if pos > 0x3fffff: pos = 0x3fffff
        self.write(Register.XTARGET, pos)

    '''
    # same as go to but with a forced direction
    def goToDir(self, dir, pos):
        self.xfer(LReg.GOTO_DIR)
        if pos > 0x3fffff: pos = 0x3fffff
        self.xfer(pos >> 16)
        self.xfer(pos >> 8)
        self.xfer(pos)

    # sets the hardstop option for the limit switch
    def setLimitHardStop(self, stop):
        if stop == 1: self.setParam([0x1A, 16], 0x3608)
        if stop == 0: self.setParam([0x1A, 16], 0x3618)

    # go until switch press event occurs
    def goUntilPress(self, act, dir, spd):
        self.xfer(LReg.GO_UNTIL | act | dir)
        if spd > 0x3fffff: spd = 0x3fffff
        self.xfer(spd >> 16)
        self.xfer(spd >> 8)
        self.xfer(spd)

    def getSwitch(self):
        if self.getStatus() & 0x4: return 1
        else: return 0

    # go until switch release event occurs
    def goUntilRelease(self, act, dir):
        self.xfer(LReg.RELEASE_SW | act | dir)

    # reads the value of the switch
    def readSwitch(self):
        if self.getStatus() & 0x4: return 1
        else: return 0

    # go home
    def goHome(self):
        self.xfer(LReg.GO_HOME)

    # go to mark position
    def goMark(self):
        self.xfer(LReg.GO_MARK)

    # set mark point
    def setMark(self, value):

        if value == 0: value = self.getPosition()
        self.xfer(LReg.MARK)
        if value > 0x3fffff: value = 0x3fffff
        if value < -0x3fffff: value = -0x3fffff

        self.xfer(value >> 16)
        self.xfer(value >> 8)
        self.xfer(value)

    # set current position to the home position
    def setAsHome(self):
        self.xfer(LReg.RESET_POS)

    # reset the device to initial conditions
    def resetDev(self):
        self.xfer(LReg.RESET_DEVICE)
        if self.boardInUse == 1: self.setParam([0x1A, 16], 0x3608)
        if self.boardInUse == 0: self.setParam([0x1A, 16], 0x3608)

    # stop the motor using the decel
    def softStop(self):
        self.xfer(LReg.SOFT_STOP)

    # hard stop the motor without concern for decel curve
    def hardStop(self):
        self.xfer(LReg.HARD_STOP)

    # decelerate the motor and the disable hold
    def softFree(self):
        self.xfer(LReg.SOFT_HIZ)

    # disable hold
    def free(self):
        self.xfer(LReg.HARD_HIZ)

    # get the status of the motor
    def getStatus(self):
        temp = 0;
        self.xfer(LReg.GET_STATUS)
        temp = self.xfer(0) << 8
        temp += self.xfer(0)
        return temp

    # calculates the value of the ACC register
    def accCalc(self, stepsPerSecPerSec):
        temp = float(stepsPerSecPerSec) * 0.137438
        if temp > 4095.0: return 4095
        else: return round(temp)

    # calculated the value of the DEC register
    def decCalc(self, stepsPerSecPerSec):
        temp = float(stepsPerSecPerSec) * 0.137438
        if temp > 4095.0: return 4095
        else: return round(temp)

    # calculates the max speed register
    def maxSpdCalc(self, stepsPerSec):
        temp = float(stepsPerSec) * 0.065536
        if temp > 1023.0: return 1023
        else: return round(temp)

    # calculates the min speed register
    def minSpdCalc(self, stepsPerSec):
        temp = float(stepsPerSec) * 4.1943
        if temp > 4095.0: return 4095
        else: return round(temp)

    # calculates the value of the FS speed register
    def fsCalc(self, stepsPerSec):
        temp = (float(stepsPerSec) * 0.065536) - 0.5
        if temp > 1023.0: return 1023
        else: return round(temp)

    # calculates the value of the INT speed register
    def intSpdCalc(self, stepsPerSec):
        temp = float(stepsPerSec) * 4.1943
        if temp > 16383.0: return 16383
        else: return round(temp)

    # calculate speed
    def spdCalc(self, stepsPerSec):
        temp = float(stepsPerSec) * 67.106
        if temp > float(0x000fffff): return 0x000fffff
        else: return round(temp)

    '''

    # Read data from the SPI bus
    def read(self, address, data):
        self.sendData(address, data)
        readValue = sBoard.spi.readbytes(5)
        # return self.convert(self.param(readValue))
        value = readValue[1]
        value = value << 8
        value |= readValue[2]
        value = value << 8
        value |= readValue[3]
        value = value << 8
        value |= readValue[4]

        return value

    # Write data to the SPI bus
    def write(self, address, data):
        # For write, add 0x80 to address
        address = address | 0x80
        print('0x{:02x}'.format(address))
        self.sendData(address, data)

    # Send data to the SPI bus
    def sendData(self, address, data):
        # Initialize datagram variable
        datagram = 0

        # Delay 100 us
        time.sleep(0.0001)

        # Begin transmission by pulling CS pin low
        # gpio.output(self.chipSelect, gpio.LOW)

        # Delay 10 us before sending data
        time.sleep(0.00001)

        # Send data 8 bits at a time
        # self.xfer(address)
        # self.xfer(data >> 24)
        # self.xfer(data >> 16)
        # self.xfer(data >> 8)
        # self.xfer(data)

        # datagram |= self.xfer((data >> 24))
        # datagram <<= 8
        # datagram |= self.xfer((data >> 16))
        # datagram <<= 8
        # datagram |= self.xfer((data >> 8))
        # datagram <<= 8
        # datagram |= self.xfer((data))

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

        # Refactor response for a readable integer and hex
        # response = int(''.join(map(str,response)))

        # return response

    def xfer(self, data):

        # Mask the value to a byte format for transmision
        data = (int(data) & 0xff)

        #toggle chip select and SPI transfer
        # gpio.output(self.chipSelect, gpio.LOW)
        # gpio.output(self.chipSelect, gpio.HIGH)

        # Get response back from SPI transfer
        response = sBoard.spi.xfer2([data])

        return response[0]

    ''' All these need to be updated
    # set a parameter of the motor driver
    def setParam(self, param, value):
        self.xfer(LReg.SET_PARAM | param[0])
        return self.paramHandler(param, value)
    '''

    '''
    # Get a parameter from the motor driver
    def getParam(self, param):
        self.xfer(LReg.GET_PARAM | param[0])
        return self.paramHandler(param, 0)
    '''

    # Convert twos compliment
    def convert(self, val):
        if val > 0x400000/2:
            val = val - 0x400000
        return val

    '''
    # Switch case to handle parameters
    def paramHandler(self, param, value):
        return self.param(value, param[1])

    # Utility function
    def param(self, value):
        ret_value = 0

        bit_len = 40

        byte_len = bit_len/8
        if (bit_len%8 > 0): byte_len +=1

        mask = 0xffffffff >> (32 - bit_len)
        if value > mask: value = mask

        if byte_len >= 4.0:
            temp = self.xfer(value >> 24)
            ret_value |= temp << 24
        if byte_len >= 3.0:
            temp = self.xfer(value >> 16)
            ret_value |= temp << 16
        if byte_len >= 2.0:
            temp = self.xfer(value >>8)
            ret_value |= temp << 8
        if byte_len >= 1.0:
            temp = self.xfer(value)
            ret_value |= temp

        return (ret_value & mask)
    '''
