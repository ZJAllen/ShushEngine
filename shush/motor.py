__author__ = 'ZJAllen'

from shush.boards import Board, s1, gpio
from shush.drivers import tmc5160_reg as reg
import time


class Motor(Board):

    def __init__(self, motor: int):
        # Setting the CS and enable pins according to the motor number called

        if motor == 0:
            self.chip_select = s1.m0_cs
            self.enable = s1.m0_enable
        if motor == 1:
            self.chip_select = s1.m1_cs
            self.enable = s1.m1_enable
        if motor == 2:
            self.chip_select = s1.m2_cs
            self.enable = s1.m2_enable
        if motor == 3:
            self.chip_select = s1.m3_cs
            self.enable = s1.m3_enable
        if motor == 4:
            self.chip_select = s1.m4_cs
            self.enable = s1.m4_enable
        if motor == 5:
            self.chip_select = s1.m5_cs
            self.enable = s1.m5_enable

        # Initially apply default settings.
        # These can be configured at any time.
        self.default_settings()

    def enable_motor(self):
        # Pull Enable pin LOW to enable motor

        gpio.output(self.enable, gpio.LOW)

    def diable_motor(self):
        # Pull Enable pin HIGH to disable motor

        gpio.output(self.enable, gpio.HIGH)

    def default_settings(self):
        # Set default motor parameters

        # MULTISTEP_FILT = 1, EN_PWM_MODE = 1 enables stealthChop
        self.write(reg.GCONF, 0x0000000C)
        # TOFF = 3, HSTRT = 4, HEND = 1, TBL = 2, CHM = 0 (spreadCycle)
        self.write(reg.CHOPCONF, 0x000100C3)
        # IHOLD = 2, IRUN = 15 (max current), IHOLDDELAY = 8
        self.write(reg.IHOLD_IRUN, 0x00080F02)
        # TPOWERDOWN = 10: Delay before powerdown in standstill
        self.write(reg.TPOWERDOWN, 0x0000000A)
        # TPWMTHRS = 500
        self.write(reg.TPWMTHRS, 0x000001F4)

        self.write_ramp_params()

        # Position mode
        self.write(reg.RAMPMODE, 0)
        # Set current position to 0
        self.write(reg.XACTUAL, 0)
        # Set XTARGET to 0, which holds the motor at the current position
        self.write(reg.XTARGET, 0)

    # TODO: add some more functionality...
    # Add stallGuard + coolStep (datasheet page 52)

    def set_ramp_params(self, VSTART=1, A1=25000, V1=250000, AMAX=50000, VMAX=500000, DMAX=50000, D1=50000, VSTOP=10):
        # Set parameters for position ramp generator
        # If needed, modify these before using self.go_to() or other positions

        Motor.set_ramp_params.VSTART = VSTART
        Motor.set_ramp_params.A1 = A1
        Motor.set_ramp_params.V1 = V1
        Motor.set_ramp_params.AMAX = AMAX
        Motor.set_ramp_params.VMAX = VMAX
        Motor.set_ramp_params.DMAX = DMAX
        Motor.set_ramp_params.D1 = D1
        Motor.set_ramp_params.VSTOP = VSTOP

    def write_ramp_params(self):
        # Gets values from set_ramp_params() and writes them to their registers

        self.set_ramp_params()

        self.write(reg.VSTART, self.set_ramp_params.VSTART)
        self.write(reg.A1, self.set_ramp_params.A1)
        self.write(reg.V1, self.set_ramp_params.V1)
        self.write(reg.AMAX, self.set_ramp_params.AMAX)
        self.write(reg.VMAX, self.set_ramp_params.VMAX)
        self.write(reg.DMAX, self.set_ramp_params.DMAX)
        self.write(reg.D1, self.set_ramp_params.D1)
        self.write(reg.VSTOP, self.set_ramp_params.VSTOP)

    def enable_switch(self, direction: int):
        # Configure limit switch.
        # See datasheet for limit switch config default_settings

        # Initialize list
        setting_array = [0] * 12

        # en_softstop = 1
        setting_array[0] = 1

        if direction == 1:
            setting_array[6] = 1     # latch_l_active = 1
            setting_array[11] = 1    # stop_l_enable = 1
            error = False
        elif direction == 2:
            setting_array[4] = 1     # latch_r_active = 1
            setting_array[10] = 1    # stop_r_enable = 1
            error = False
        else:
            print("Not a valid input! Please use 1 (left), or 2 (right).")
            error = True

        if not error:
            # Create binary string, to be correctly sent over SPI
            switch_settings = int(''.join(str(i) for i in setting_array), 2)
            self.write(reg.SWMODE, switch_settings)

    def get_position(self) -> int:
        # Returns the current position of the motor relative to Home (0)

        current_position = self.read(reg.XACTUAL)

        # Convert 2's complement to get signed number
        current_position = self.twos_comp(current_position)

        return current_position

    def get_latched_position(self) -> int:
        # Returns the latched position when using limit switches.

        latched_position = self.read(reg.XLATCH)

        # Convert 2's complement to get signed number
        latched_position = self.twos_comp(latched_position)

        return latched_position

    def get_velocity(self) -> int:
        # Returns the current velocity of the motor (+ or -)

        current_velocity = self.read(reg.VACTUAL)

        # Convert 2's complement to get signed number
        # VACTUAL is valid for +-(2^23)-1, so 24 bits
        # 24 bits optional argument
        current_velocity = self.twos_comp(current_velocity, 24)

        return current_velocity

    def go_to(self, position: int):
        # Move to an absolute position relative to Home (0).

        self.position_mode()

        # Position range is from -2^31 to +(2^31)-1
        maximum_position = (2**31) - 1
        minimum_position = -(2**31)

        # Check if position is within bounds
        if position > maximum_position:
            position = maximum_position
            print("Maximum position reached! Stopped at max value.")
        elif position < minimum_position:
            position = minimum_position
            print("Minimum position reached! Stopped at min value.")

        self.write(reg.XTARGET, position)

    def calibrateHome(self, direction: int):
        # Calibrate home by driving motor to limit switch.
        # This is position-based rather than velocity based
        # Direction: use 1 for left, 2 for right

        self.enable_switch(direction)

        # If the switch is active, move away from the switch until inactive
        self.get_ramp_status()

        switch_pressed = int(self.get_ramp_status.status_stop_l)

        if direction == 1:
            error = False

            switch_pressed = int(self.get_ramp_status.status_stop_l)

            if switch_pressed == 1:

                # Move away from switch
                self.go_to(512000)

                while switch_pressed == 1:
                    self.get_ramp_status()
                    switch_pressed = int(self.get_ramp_status.status_stop_l)

        elif direction == 2:
            error = False

            switch_pressed = int(self.get_ramp_status.status_stop_r)

            if switch_pressed == 1:

                # Move away from switch
                self.go_to(-512000)

                while switch_pressed == 1:
                    self.get_ramp_status()
                    switch_pressed = int(self.get_ramp_status.status_stop_r)

        else:
            print("Command not processed!")
            error = True

        if not error:
            self.go_to(-2560000)

            # Delay to let the motor ramp from standstill
            time.sleep(0.1)

            # Poll VACTUAL until it is 0
            actual_velocity = self.get_velocity()

            while actual_velocity != 0:
                # time.sleep(0.001)
                actual_velocity = self.get_velocity()

            # Engage hold mode
            self.hold_mode()

            # Calcuate difference between latched position and actual position
            actual_position = self.get_position()
            latched_position = self.get_latched_position()

            position_difference = actual_position - latched_position

            # Write position_difference to XACTUAL to set home position
            self.write(reg.XACTUAL, position_difference)

            # Clear status_latch_l
            self.write(reg.RAMPSTAT, 4)

            # Go to 0 position: the exact position of switch activation
            self.go_to(0)

            print("Homing complete!")

    def move_velocity(self, dir: int, v_max: int = 500000, a_max: int = 50000):
        # Drive movor in velocity mode, positive or negative

        self.write(reg.VMAX, v_max)
        self.write(reg.AMAX, a_max)

        if dir == 0:
            velocity_mode = 1
            error = False
        elif dir == 1:
            velocity_mode = 2
            error = False
        else:
            print("Not a valid input! Please use 'right', or 'left'.")
            error = True

        if not error:
            self.write(reg.RAMPMODE, velocity_mode)

    def hold_mode(self):
        self.write(reg.RAMPMODE, 3)

    def position_mode(self):
        self.write(reg.RAMPMODE, 0)

    def get_ramp_status(self):
        self.read(reg.RAMPSTAT)

        ramp_status = self.read(reg.RAMPSTAT)

        ramp_status_binary = "{0:014b}".format(ramp_status)
        ramp_status_array = list(ramp_status_binary)

        # Parse response so individual registers can be referenced
        Motor.get_ramp_status.status_sg = ramp_status_array[0]
        Motor.get_ramp_status.second_move = ramp_status_array[1]
        Motor.get_ramp_status.t_zerowait_active = ramp_status_array[2]
        Motor.get_ramp_status.vzero = ramp_status_array[3]
        Motor.get_ramp_status.position_reached = ramp_status_array[4]
        Motor.get_ramp_status.velocity_reached = ramp_status_array[5]
        Motor.get_ramp_status.event_pos_reached = ramp_status_array[6]
        Motor.get_ramp_status.event_stop_sg = ramp_status_array[7]
        Motor.get_ramp_status.event_stop_r = ramp_status_array[8]
        Motor.get_ramp_status.event_stop_l = ramp_status_array[9]
        Motor.get_ramp_status.status_latch_r = ramp_status_array[10]
        Motor.get_ramp_status.status_latch_l = ramp_status_array[11]
        Motor.get_ramp_status.status_stop_r = ramp_status_array[12]
        Motor.get_ramp_status.status_stop_l = ramp_status_array[13]

    def read(self, address: int) -> int:
        # Read data from the SPI bus.

        # Pre-populate data buffer with an empty array/list
        address_buffer = [0] * 5
        read_buffer = [0] * 5

        # Clear write bit
        address_buffer[0] = address & 0x7F

        self.send_data(address_buffer)

        # It will look like [address, 0, 0, 0, 0]
        read_buffer = self.send_data(address_buffer)

        # Parse data returned from SPI transfer/read
        value = read_buffer[1]
        value = value << 8
        value |= read_buffer[2]
        value = value << 8
        value |= read_buffer[3]
        value = value << 8
        value |= read_buffer[4]

        return value

    def write(self, address: int, data: int) -> int:
        # Write data to the SPI bus.

        # Pre-populate data buffer with an empty array/list
        write_buffer = [0] * 5

        # For write access, add 0x80 to address
        write_buffer[0] = address | 0x80

        write_buffer[1] = 0xFF & (data >> 24)
        write_buffer[2] = 0xFF & (data >> 16)
        write_buffer[3] = 0xFF & (data >> 8)
        write_buffer[4] = 0xFF & data

        return self.send_data(write_buffer)

    def send_data(self, data_array: list) -> int:
        # Send data (read/write) over the SPI bus.
        # Pulls CS Low, transfers data array, then pulls CS High

        # Begin transmission by pulling CS pin low
        gpio.output(self.chip_select, gpio.LOW)

        # Send data
        response = Board.spi.xfer2(data_array)

        # End transmission by pulling CS pin HIGH
        gpio.output(self.chip_select, gpio.HIGH)

        return response

    def twos_comp(self, value: int, bits: int = 32) -> int:
        if (value & (1 << (bits - 1))) != 0:
            signed_value = value - (1 << bits)
        else:
            signed_value = value

        return signed_value
