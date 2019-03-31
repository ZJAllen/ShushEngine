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

        # IHOLD = 2, IRUN = 15 (max current), IHOLDDELAY = 8
        self.write(Register.IHOLD_IRUN, 0x00080F02)

        # TPOWERDOWN = 10: Delay before powerdown in standstill
        self.write(Register.TPOWERDOWN, 0x0000000A)

        #TPWMTHRS = 500
        self.write(Register.TPWMTHRS, 0x000001F4)

        self.writeRampParams()

        self.write(Register.RAMPMODE, 0)    # Position mode
        self.write(Register.XACTUAL, 0)     # Set current position to 0
        self.write(Register.XTARGET, 0)     # Set XTARGET to 0, which holds the motor at the current position

    # TODO: add some more functionality...
    ## Add stallGuard + coolStep (datasheet page 52)
    
    # Set parameters for position ramp generator
    # If needed, modify these before using self.goTo() or other positioning
    def setRampParams(self, VSTART = 1, A1 = 25000, V1 = 250000, AMAX = 50000, VMAX = 500000, DMAX = 50000, D1 = 50000, VSTOP = 10):
        Motor.setRampParams.VSTART = VSTART
        Motor.setRampParams.A1 = A1
        Motor.setRampParams.V1 = V1
        Motor.setRampParams.AMAX = AMAX
        Motor.setRampParams.VMAX = VMAX
        Motor.setRampParams.DMAX = DMAX
        Motor.setRampParams.D1 = D1
        Motor.setRampParams.VSTOP = VSTOP
    
    # Gets values from setRampParams() and writes them to the appropriate registers
    def writeRampParams(self):
        self.setRampParams()

        self.write(Register.VSTART, self.setRampParams.VSTART)
        self.write(Register.A1, self.setRampParams.A1)
        self.write(Register.V1, self.setRampParams.V1)
        self.write(Register.AMAX, self.setRampParams.AMAX)
        self.write(Register.VMAX, self.setRampParams.VMAX)
        self.write(Register.DMAX, self.setRampParams.DMAX)
        self.write(Register.D1, self.setRampParams.D1)
        self.write(Register.VSTOP, self.setRampParams.VSTOP)

    # Configure limit switch. See datasheet for limit switch config defaultSettings
    def enableSwitch(self, direction):
        # Initialize list
        settingArray = [0] * 12

        # en_softstop = 1
        settingArray[0] = 1

        if direction == 'left':
            settingArray[6] = 1     # latch_l_active = 1
            settingArray[11] = 1    # stop_l_enable = 1
            error = False
        elif direction == 'right':
            settingArray[4] = 1     # latch_r_active = 1
            settingArray[10] = 1    # stop_r_enable = 1
            error = False
        else:
            print("Not a valid input! Please use 'right', or 'left'.")
            error = True

        if not error:
            # Create binary string, so it can be correctly processed and sent over SPI
            switchSettings = int(''.join(str(i) for i in settingArray), 2)
            self.write(Register.SWMODE, switchSettings)

    # Get the posistion of the motor
    def getPosSigned(self):
        currentPos = self.read(Register.XACTUAL)

        # Convert 2's complement to get signed number
        currentPos = self.twosComp(currentPos)

        #print("Current Pos: ", currentPos)

        return currentPos

    def getLatchSigned(self):
        latchedPos = self.read(Register.XLATCH)

        # Convert 2's complement to get signed number
        latchedPos = self.twosComp(latchedPos)

        return latchedPos

    def getVelSigned(self):
        currentVel = self.read(Register.VACTUAL)

        # Convert 2's complement to get signed number
        # VACTUAL is valid for +-(2^23)-1, so 24 bits
        currentVel = self.twosComp(currentVel, 24)  # 24 bits optional argument

        return currentVel

    # Move to an absolute position from Home (0) position
    def goTo(self, pos):
        self.posMode()

        # Position range is from -2^31 to +(2^31)-1
        maxPos = (2**31) - 1
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
    ## Position-based rather than velocity based
    def calibrateHome(self, direction):
        self.enableSwitch(direction)

        # If the switch is active (pressed), move away from the switch until unactive
        self.getRampStat()

        switchPressed = int(self.getRampStat.status_stop_l)

        if direction == 'left':
            error = False

            switchPressed = int(self.getRampStat.status_stop_l)

            if switchPressed == 1:

                # Move away from switch
                self.goTo(512000)

                while switchPressed == 1:
                    self.getRampStat()
                    switchPressed = int(self.getRampStat.status_stop_l)

        elif direction ==  'right':
            error = False

            switchPressed = int(self.getRampStat.status_stop_r)

            if switchPressed == 1:

                # Move away from switch
                self.goTo(-512000)

                while switchPressed == 1:
                    self.getRampStat()
                    switchPressed = int(self.getRampStat.status_stop_r)

        else:
            print("Command not processed!")
            error = True

        if not error:
            self.goTo(-2560000)

            # Delay to let the motor ramp from standstill
            time.sleep(0.1)

            # Poll VACTUAL until it is 0
            velActual = self.getVelSigned()

            while velActual != 0:
                #time.sleep(0.001)
                velActual = self.getVelSigned()
                #print("Velocity: ", velActual)

            # Engage hold mode
            self.holdMode()

            # Calcuate difference between latched position and actual position
            actualPos = self.getPosSigned()
            latchedPos = self.getLatchSigned()

            posDifference = actualPos - latchedPos

            # Write posDifference to XACTUAL to set home position
            self.write(Register.XACTUAL, posDifference)

            # Clear status_latch_l
            self.write(Register.RAMPSTAT,4)

            # Go to 0 position, which should be the exact position of switch activation
            self.goTo(0)

            print("Homing complete!")


    # Drive movor in velocity mode, positive or negative
    def moveVelocity(self, dir, vmax = 500000, amax = 50000):
        self.write(Register.VMAX, vmax)
        self.write(Register.AMAX, amax)
        if dir == 'left':
            velMode = 1
            error = False
        elif dir == 'right':
            velMode = 2
            error = False
        else:
            print("Not a valid input! Please use 'right', or 'left'.")
            error = True

        if not error:
            self.write(Register.RAMPMODE, velMode)

    def holdMode(self):
        self.write(Register.RAMPMODE, 3)

    def posMode(self):
        self.write(Register.RAMPMODE, 0)

    def getRampStat(self):
        self.read(Register.RAMPSTAT)
        rampStat = self.read(Register.RAMPSTAT)
        rampStatBinary = "{0:014b}".format(rampStat)
        rampStatArray = list(rampStatBinary)

        # Parse response so individual registers can be referenced
        Motor.getRampStat.status_sg         = rampStatArray[0]
        Motor.getRampStat.second_move       = rampStatArray[1]
        Motor.getRampStat.t_zerowait_active = rampStatArray[2]
        Motor.getRampStat.vzero             = rampStatArray[3]
        Motor.getRampStat.position_reached  = rampStatArray[4]
        Motor.getRampStat.velocity_reached  = rampStatArray[5]
        Motor.getRampStat.event_pos_reached = rampStatArray[6]
        Motor.getRampStat.event_stop_sg     = rampStatArray[7]
        Motor.getRampStat.event_stop_r      = rampStatArray[8]
        Motor.getRampStat.event_stop_l      = rampStatArray[9]
        Motor.getRampStat.status_latch_r    = rampStatArray[10]
        Motor.getRampStat.status_latch_l    = rampStatArray[11]
        Motor.getRampStat.status_stop_r     = rampStatArray[12]
        Motor.getRampStat.status_stop_l     = rampStatArray[13]
        #print("Ramp Stat: ", rampStatBinary)

    # Read data from the SPI bus
    def read(self, address):
        # Pre-populate data buffer with an empty array/list
        addressBuf = [0] * 5
        readBuf = [0] * 5

        # Clear write bit
        addressBuf[0] = address & 0x7F

        self.sendData(addressBuf)
        readBuf = self.sendData(addressBuf)  # It will look like [address, 0, 0, 0, 0]

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

        response = self.sendData(writeBuf)

    # Send data by pulling CS Low, transfer data array (write -> read), then pull CS High
    def sendData(self, dataArray):

        # Begin transmission by pulling CS pin low
        gpio.output(self.chipSelect, gpio.LOW)

        # Send data
        response = Board.spi.xfer2(dataArray)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chipSelect, gpio.HIGH)

        return response

    def twosComp(self, value, bits = 32):
        if (value & (1 << (bits - 1))) != 0:
            signedValue = value - (1 << bits)
        else:
            signedValue = value

        return signedValue
