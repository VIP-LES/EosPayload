import Adafruit_BBIO.GPIO as GPIO
import time
import busio
import logging
import board
from adafruit_ms8607 import MS8607
from adafruit_blinka.board.beagleboard.beaglebone_black import *

#GPIO.setup("P9_16", GPIO.OUT)


i2c = busio.I2C(board.SCL, board.SDA)
#i2c = busio.I2C(pin.I2C1_SCL, pin.I2C1_SDA)
ms = MS8607(i2c)





while True:
    f = open('/EosPayload/drivers/sensor_packages/help.csv','a')
    GPIO.output("P9_18", GPIO.HIGH)
    time.sleep(0.5)
    f.write(ms.temperature)
    GPIO.output("P9_18", GPIO.LOW)
    time.sleep(0.5)
    GPIO.cleanup()


    f.close()

    
