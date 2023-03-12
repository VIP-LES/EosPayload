import Adafruit_BBIO.GPIO as GPIO
import time
import busio
import logging
import board
from adafruit_ms8607 import MS8607

GPIO.setup("P9_16", GPIO.OUT)


i2c = busio.I2C(2, board.SCL, board.SDA)
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

    
