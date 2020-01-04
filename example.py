import shush
import time

m = shush.Motor(0)
m.enable_motor()


# This function takes the target position as an input.
# It prints the current position and the iteration.
# The motor spins until it gets to the target position
# before allowing the next command.
def spin(target):
    m.go_to(target)

    i = 0

    while m.get_position() != target:
        print(m.get_position())
        print(i)
        i += 1


while(True):
    # Spin 5 rotations from start
    spin(256000)

    time.sleep(0.5)
    # Spin back 5 rotations to starting point
    spin(0)

    time.sleep(0.5)
