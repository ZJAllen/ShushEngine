__author__ = 'ZJAllen'

from Shush.Board import *
from Shush.Drivers import TMC5160_Registers as Register
import math
import time

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

        self.write(Register.RAMPMODE, 0)    # Position mode
        self.write(Register.XACTUAL, 0)     # Set current position to 0
        self.write(Register.XTARGET, 0)     # Set XTARGET to 0, which holds the motor at the current position

    # TODO: add some more functionality...

    # Configure limit switch. See datasheet for limit switch config defaultSettings
    def enableSwitch(self, direction):
        # Initialize list
        settingArray = [0] * 11

        # en_softstop = 1
        settingArray[1] = 0

        if direction = "left":
            settingArray[7] = 1     # latch_l_active = 1
            settingArray[11] = 1    # stop_l_active = 1
        elif direction = "right":
            settingArray[5] = 1     # latch_r_active = 1
            settingArray[10] = 1    # stop_r_active = 1
        else:
            print("Not a valid input! Please use ‘right’, or ‘left.")
            error = True

        if not error:
            switchSettings = int("".join(settingArray))
            self.write(Register.SWMODE, switchSettings)

    # Get the posistion of the motor
    def getPos(self):
        currentPos = self.read(Register.XACTUAL)
        print("Current Pos: ", currentPos)

        return currentPos

    def getVel(self):
        currentVel = self.read(Register.VACTUAL)

        return currentVel

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

    # Calibrate home by driving motor to limit switch
    def calibrateHome(self, direction):
        enableSwitch(direction)

        # If the switch is active (pressed), move away from the switch until unactive
        getRampStat()

        if direction = "left":
            while getRampStat.status_stop_l = 1:
                # Move away from switch
                moveVelocity("right")
        elif direction =  "right":
            while getRampStat.status_stop_r = 1:
                # Move away from switch
                moveVelocity("left")
        else:
            print("Command not processed!")
            error = True

        if not error:
            moveVelocity(direction)

            # Delay to let the motor ramp from 0 velocity
            time.sleep(0.01)

            if self.read(Register.VACTUAL) == 0:
                # Engage hold mode
                holdMode()

                # Calcuate difference between latched position and actual position
                actualPos = getPos()
                latchedPos = self.read(Register.XLATCH)

                posDifference = actualPos - latchedPos

                # Write posDifference to XACTUAL to set home position
                self.write(Register.XACTUAL, posDifference)

                # Go to 0 position, which should be the exact position of switch activation
                goTo(0)

    # Drive movor in velocity mode, positive or negative
    def moveVelocity(self, dir, vmax = 5000, amax = 5000):
        self.write(Register.VMAX, vmax)
        self.write(Register.AMAX, amax)
        if dir = "left":
            velMode = 2
        elif dir = "right":
            velMode = 3
        else:
            print("Not a valid input! Please use ‘right’, or ‘left.")
            error = True

        if not error:
            self.write(Register.RAMPMODE, velMode)

    def holdMode(self):
        self.write(Register.RAMPMODE, 3)

    def getRampStat(self):
        rampStat = self.read(Register.RAMPSTAT)
        rampStatBinary = "{0:014b}".format(rampstat)
        rampStatArray = list(rampStatBinary)

        # Parse response so individual registers can be referenced
        getRampStat.status_sg           = rampStatArray[0]
        getRampStat.second_move         = rampStatArray[1]
        getRampStat.t_zerowait_active   = rampStatArray[2]
        getRampStat.vzero               = rampStatArray[3]
        getRampStat.position_reached    = rampStatArray[4]
        getRampStat.velocity_reached    = rampStatArray[5]
        getRampStat.event_pos_reached   = rampStatArray[6]
        getRampStat.event_stop_sg       = rampStatArray[7]
        getRampStat.event_stop_r        = rampStatArray[8]
        getRampStat.event_stop_l        = rampStatArray[9]
        getRampStat.status_latch_r      = rampStatArray[10]
        getRampStat.status_latch_l      = rampStatArray[11]
        getRampStat.status_stop_r       = rampStatArray[12]
        getRampStat.status_stop_l       = rampStatArray[13]

    # Read data from the SPI bus
    def read(self, address):
        # Pre-populate data buffer with an empty array/list
        addressBuf = [0] * 5
        readBuf = [0] * 5

        # Clear write bit
        addressBuf[0] = address & 0x7F

        readBuf = sendData(addressBuf)  # It will look like [address, 0, 0, 0, 0]

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
        # Pre-populate data buffer with an empty array/list
        writeBuf = [0] * 5

        # For write access, add 0x80 to address
        writeBuf[0] = address | 0x80

        writeBuf[1] = 0xFF & (data >> 24)
        writeBuf[2] = 0xFF & (data >> 16)
        writeBuf[3] = 0xFF & (data >> 8)
        writeBuf[4] = 0xFF & data

        sendData(writeBuf)

    # Send data by pulling CS Low, transfer data array (write -> read), then pull CS High
    def sendData(self, dataArray):

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send data
        response = sBoard.spi.xfer2(dataArray)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chipSelect, gpio.HIGH)

        return response
