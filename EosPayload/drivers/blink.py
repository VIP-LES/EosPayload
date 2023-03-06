import Adafruit_BBIO.GPIO as GPIO
import time

GPIO.setup("P9_18", GPIO.OUT)

while True:
    GPIO.output("P9_18", GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output("P9_18", GPIO.LOW)
    time.sleep(0.5)
