# Eos Payload Module 

---
## About
Eos is the software platform for Georgia Tech's "Lightning from the Edge of Space" high-altitude ballooning project under the VIP program.  This module defines the payload software.  


## Installation
1. Install python >= 3.10 and add to PATH
2. Clone the repo: `git clone https://github.com/VIP-LES/EosPayload.git`
3. Initialize virtual env: `python -m venv venv` (PyCharm can also do this for you)
4. Run `source ./venv/bin/activate` (linux / mac) or `.\venv\Scripts\activate` (windows).  You'll have to do this every time you want to enter the venv. 
5. Install dependencies: `pip install -r requirements.txt` 
6. Install Eclipse Mosquitto: https://mosquitto.org/download/

Note: to exit the venv, run `deactivate`

## Running EosPayload
Prereq: Start the MQTT server by running mosquitto.  Use -v to allow it   (Windows Example: `C:\Program Files\mosquitto -v`)

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
- DriverBase offers two threads for Drivers to implement: device_read() and device_command().  Most drivers will not need to use both

### Adding Dependencies
- In your terminal in your venv, run `pip install <your dependency>`
- Run `pip freeze` and compare the result to `requirements.txt`.  Add any new lines from the `pip freeze` output to the requirements.txt file
- You should now be able to `import <your dependency>` in your EosPayload python files

### Debugging
Pycharm allows you to set breakpoints and inspect variables mid-execution.  Reference the "Run From PyCharm" instructions above, but run the configuration in debug mode
