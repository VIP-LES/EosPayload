# Eos Payload Module 

---
## About
Eos is the software platform for Georgia Tech's "Lightning from the Edge of Space" high-altitude ballooning project under the VIP program.  This module defines the payload software.  


## Installation
1. Install python >= 3.10 and add to PATH
2. Clone the repo: `git clone https://github.com/VIP-LES/EosPayload.git`
3. Initialize virtual env: `python -m venv venv` (PyCharm can also do this for you)
4. Run `source ./venv/bin/activate` (linux / mac) or `.\venv\Scripts\activate` (windows).  You'll have to do this every time you want to enter the venv. 
5. Install dependencies: `pip install -r requirements.txt`.  On Windows where some dependencies can't be installed, this command may be useful: `FOR /F %k in (requirements.txt) DO ( if NOT # == %k ( pip install %k ) )` 
6. Install Eclipse Mosquitto: https://mosquitto.org/download/

Note: to exit the venv, run `deactivate`

## Mosquitto MQTT
EosPayload relies on the mosquitto MQTT broker for communication between devices.  When you install mosquitto you get 3 command line tools:
- `mosquitto` - run the server.  Use -v to log requests to console.  
Windows Example: `C:\Program Files\mosquitto -v`  
Mac Example: `brew services start mosquitto -v`
- `mosquitto_sub` - a simple topic subscriber tool that is useful for seeing what MQTT messages are being published.  
Windows example: `"C:\Program Files\mosquitto\mosquitto_sub.exe" -V 5 -q 2 -t # -v`
- `mosquitto_pub` - a simple message publish tool that is also useful for sending test MQTT messages to your device.
Windows example: `"C:\Program Files\mosquitto\mosquitto_pub.exe" -t "health/heartbeat" -m "yo" -q 2`  

Note: for the sub/pub tools to work on Mac you may need to run `brew link mosquitto` first  

More info on the command line tools can be found here: https://mosquitto.org/man/

## Running EosPayload
Pre-req: Start the MQTT server by running mosquitto (see above)

### From Terminal
1. Navigate to your EosPayload repository root using the `cd` command (all OS's)
2. Enter your venv (see command above)
3. Run `python -m EosPayload`

### From PyCharm
1. Create a new Python Run Configuration
2. Set the script path to `{repository root}\EosPayload\__main__.py`
3. Set the python interpreter to the Python 3.10 from your venv
4. Set the working directory to your EosPayload repository root
5. Run the configuration

### Output
- Driver data logged via the provider DriverBase function is output into `<device-id>.dat`
- Driver log messages are output into `<device-id>.log`
- OrchEOStrator logs are output into `orchEOStrator.log`
- All log messages are output to the terminal / pycharm console stderr stream

## Development

### General
- Do not commit directly to main.  You must create an issue, make a branch, make a PR, and get it reviewed and approved.
- If you make a PR for the first time, add yourself to `CONTRIBUTORS.md` in your PR.

### Adding Drivers
- Add all new drivers to `EosPayload/drivers`.
- You must extend DriverBase or a derivative of DriverBase, which provide several functions out-of-the-box to simplify development and multithreading.
- Keep the driver runner code tidy.  Consider making a file or module in `EosPayload/Lib` to put your logic
- DriverBase allows for multithreaded drivers.  Most drivers will need to spawn at least one extra thread.  See the docstring for `DriverBase.register_thread()`

### Configuring Payload and Drivers
Each Payload is configured with a JSON file, by default it is stored at `config.json`, though a custom path can be set 
with the `-c` field when you run EosPayload. Currently top level fields are unused, and each device is configured using 
an entry in the `devices` list.

A minimal device config requires:

| Field        | Value                                                  |
|--------------|--------------------------------------------------------|
| driver_class | The Python class that will be used to spawn the device |
| device_id    | A unique value of `EosLib.device.Device`               |
| enabled      | `true` or `false`, to enable or disable the device     |

Additionally, the following optional fields are available:

| Field    | Value                                                       |
|----------|-------------------------------------------------------------|
| name     | A plaintext name that overrides the auto-generated name     |
| settings | A JSON dict of settings that are passed to the driver class |


### Adding Dependencies
- In your terminal in your venv, run `pip install <your dependency>`
- Run `pip freeze` and compare the result to `requirements.txt`.  Add any new lines from the `pip freeze` output to the requirements.txt file
- You should now be able to `import <your dependency>` in your EosPayload python files
- To bump the EosLib version, run `pip install --upgrade --force-reinstall git+https://github.com/VIP-LES/EosLib@vX.Y.Z#egg=EosLib` (replace `X.Y.Z` with the version number)

### Debugging
Pycharm allows you to set breakpoints and inspect variables mid-execution.  Reference the "Run From PyCharm" instructions above, but run the configuration in debug mode

### Docker Installation/Use
If you plan to install/use EosPayload via docker, you can ignore all the above steps. Instead, follow these:

1. Install Docker (Instructions [here](https://docs.docker.com/get-docker/))
2. Install Docker compose (Instructions [here](https://docs.docker.com/compose/install/))
3. Clone the repo: `git clone https://github.com/VIP-LES/EosPayload.git`
4. Run `docker compose up`
5. Everything should install and run automatically

### Configuring BeagleBone Pins
If you need to change the default pin behavior, you can add `config-pin` commands to `beaglebone_pin_setup/pin_setup.sh`, which runs on startup  
