import Adafruit_BBIO.GPIO as GPIO
import time

import logging
import board
from adafruit_ms8607 import MS8607

GPIO.setup("P9_18", GPIO.OUT)


i2c = board.I2C()
ms = MS8607(i2c)





while True:
    f = open('/EosPayload/drivers/sensor_packages/help.csv','a')
    GPIO.output("P9_18", GPIO.HIGH)
    time.sleep(0.5)
    f.write(ms.temperature)
    GPIO.output("P9_18", GPIO.LOW)
    time.sleep(0.5)


    f.close()

    
