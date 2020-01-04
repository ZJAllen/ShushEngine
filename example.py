import Shush
import time

s = Shush.Board()
m = Shush.Motor(0)
m.enableMotor()


# This function takes the target position as an input.
# It prints the current position and the iteration.
# The motor spins until it gets to the target position
# before allowing the next command.
def spin(target):
    m.goTo(target)

    i = 0

    while m.getPosSigned() != target:
        print(m.getPosSigned())
        print(i)
        i += 1


while(True):
    # Spin 5 rotations from start
    spin(2560000)

    time.sleep(0.5)
    # Spin back 5 rotations to starting point
    spin(0)

    time.sleep(0.5)
