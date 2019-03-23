# ShushEngine

The Python stepper motor driver for Trinamic's TMC5160 motion controller chip.

Built from [Roboteurs](https://roboteurs.com/)'s project [SlushEngine](https://github.com/Roboteurs/slushengine)

This project is made for the Raspberry Pi only at this time.

## Getting Started

### Installing the ShushEngine project

In your Raspberry Pi, open a new Terminal window.

Change to the directory/folder in which you'd like to save your project.  For this example, let's just use the desktop.

```
cd desktop
```

To get the ShushEngine project files onto your desktop, copy/paste or type the following.

```
git clone https://github.com/ZJAllen/ShushEngine.git
```

Now, change directory into the newly created `ShushEngine` folder.

```
cd ShushEngine
```

Next, since the project is made with a structure of folders, you'll need to run the setup to tell the system where all the relative references are.

```
sudo python3 setup.py install
```

You're all ready to start using the ShushEngine!

### Simple Motor Control

The stepper motor driver chips used are [Trinamic TMC5160](https://www.trinamic.com/fileadmin/assets/Products/ICs_Documents/TMC5160_Datasheet_V1.01.pdf), which use 256 microsteps per full step.  Most common stepper motors have 200 steps per revolution, or 1.8%deg per step.  Therefore, if you want to go 1 full revolution, the TMC5160 would need a command to go 51,200 microsteps (256 * 200).  Keep this in mind for the following example.

The following example assumes the wiring according to Trinamic’s TMC5160-BOB Raspberry Pi [example](https://blog.trinamic.com/2018/02/19/stepper-motor-with-tmc5160/).

Below is a simple Python script to get the motor spinning. You can copy/paste this or type it into your favorite text editor and save it on your RPi.

``` python
import Shush
import time

m = Shush.Motor(0)

# This function takes the target position as an input.
# It prints the current position and the iteration.
# The motor spins until it gets to the target position before allowing the next command.
def spin(target):
  m.goTo(target)

  i = 0

  while m.getPos() != target:
    # The getPos() function prints the current position
    print(i)
    i += 1

while(True):
  spin(2560000) # Spin 5 rotations from start
  time.sleep(0.5)
  spin(0) # Spin back 5 rotations to starting point
  time.sleep(0.5)
```

Save this anywhere you’d like, on your Desktop for example. We’ll call it ShushExample.py. Change directory into that folder by `cd Desktop`.

Now, you can call the script by typing `python3 ShushExample.py` and the motor should start spinning.
