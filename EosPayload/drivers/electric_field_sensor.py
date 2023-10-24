from EosPayload.lib.base_drivers.driver_base import DriverBase
try:
    import Adafruit_BBIO.ADC as ADC
except ModuleNotFoundError:
    pass


class ElectricFieldSensor(DriverBase):
    adc_pin = "ENTER PIN # HERE"
    ADC.setup()
    try:
        while True:
            # Read the voltage from the ADC pin
            value = ADC.read(adc_pin)
            voltage = value * 1.8  # BeagleBone Black has a 1.8V reference voltage
            print(f"ADC Value: {value}, Voltage: {voltage:.2f} V")
    except Exception as e:
        print(f"An error occurred: {e}")
