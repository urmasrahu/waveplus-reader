# MIT License
#
# Copyright (c) 2018 Airthings AS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# https://airthings.com

# ===============================
# Module import dependencies
# ===============================

from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate
import sys
import time
import datetime
import struct
import tableprint
from led_controller import LedController, Colors

# ===============================
# Script guards for correct usage
# ===============================

if len(sys.argv) < 3:
    print ("ERROR: Missing input argument SN or SAMPLE-PERIOD.")
    print ("USAGE: read_waveplus.py SN SAMPLE-PERIOD [pipe > yourfile.txt]")
    print ("    where SN is the 10-digit serial number found under the magnetic backplate of your Wave Plus.")
    print ("    where SAMPLE-PERIOD is the time in seconds between reading the current values.")
    print ("    where [pipe > yourfile.txt] is optional and specifies that you want to pipe your results to yourfile.txt.")
    sys.exit(1)

if sys.argv[1].isdigit() is not True or len(sys.argv[1]) != 10:
    print ("ERROR: Invalid SN format.")
    print ("USAGE: read_waveplus.py SN SAMPLE-PERIOD [pipe > yourfile.txt]")
    print ("    where SN is the 10-digit serial number found under the magnetic backplate of your Wave Plus.")
    print ("    where SAMPLE-PERIOD is the time in seconds between reading the current values.")
    print ("    where [pipe > yourfile.txt] is optional and specifies that you want to pipe your results to yourfile.txt.")
    sys.exit(1)

if sys.argv[2].isdigit() is not True or int(sys.argv[2])<0:
    print ("ERROR: Invalid SAMPLE-PERIOD. Must be a numerical value larger than zero.")
    print ("USAGE: read_waveplus.py SN SAMPLE-PERIOD [pipe > yourfile.txt]")
    print ("    where SN is the 10-digit serial number found under the magnetic backplate of your Wave Plus.")
    print ("    where SAMPLE-PERIOD is the time in seconds between reading the current values.")
    print ("    where [pipe > yourfile.txt] is optional and specifies that you want to pipe your results to yourfile.txt.")
    sys.exit(1)

if len(sys.argv) > 3:
    Mode = sys.argv[3].lower()
else:
    Mode = 'terminal' # (default) print to terminal 

if Mode!='pipe' and Mode!='terminal':
    print ("ERROR: Invalid piping method.")
    print ("USAGE: read_waveplus.py SN SAMPLE-PERIOD [pipe > yourfile.txt]")
    print ("    where SN is the 10-digit serial number found under the magnetic backplate of your Wave Plus.")
    print ("    where SAMPLE-PERIOD is the time in seconds between reading the current values.")
    print ("    where [pipe > yourfile.txt] is optional and specifies that you want to pipe your results to yourfile.txt.")
    sys.exit(1)

SerialNumber = int(sys.argv[1])
SamplePeriod = int(sys.argv[2])

# ====================================
# Utility functions for WavePlus class
# ====================================

def parseSerialNumber(ManuDataHexStr):
    if (ManuDataHexStr == None or ManuDataHexStr == "None"):
        SN = "Unknown"
    else:
        ManuData = bytearray.fromhex(ManuDataHexStr)

        if (((ManuData[1] << 8) | ManuData[0]) == 0x0334):
            SN  =  ManuData[2]
            SN |= (ManuData[3] << 8)
            SN |= (ManuData[4] << 16)
            SN |= (ManuData[5] << 24)
        else:
            SN = "Unknown"
    return SN

# ===============================
# Class WavePlus
# ===============================

class WavePlus():
    def __init__(self, SerialNumber):
        self.periph        = None
        self.curr_val_char = None
        self.MacAddr       = None
        self.SN            = SerialNumber
        self.uuid          = UUID("b42e2a68-ade7-11e4-89d3-123b93f75cba")

    def connect(self):
        # Auto-discover device on first connection
        if (self.MacAddr is None):
            scanner     = Scanner().withDelegate(DefaultDelegate())
            searchCount = 0
            while self.MacAddr is None and searchCount < 50:
                devices      = scanner.scan(0.1) # 0.1 seconds scan period
                searchCount += 1
                for dev in devices:
                    ManuData = dev.getValueText(255)
                    SN = parseSerialNumber(ManuData)
                    if (SN == self.SN):
                        self.MacAddr = dev.addr # exits the while loop on next conditional check
                        break # exit for loop
            
            if (self.MacAddr is None):
                print ("ERROR: Could not find device.")
                print ("GUIDE: (1) Please verify the serial number.")
                print ("       (2) Ensure that the device is advertising.")
                print ("       (3) Retry connection.")
                sys.exit(1)
        
        # Connect to device
        if (self.periph is None):
            self.periph = Peripheral(self.MacAddr)
        if (self.curr_val_char is None):
            self.curr_val_char = self.periph.getCharacteristics(uuid=self.uuid)[0]
        
    def read(self):
        if (self.curr_val_char is None):
            print ("ERROR: Devices are not connected.")
            sys.exit(1)            
        rawdata = self.curr_val_char.read()
        rawdata = struct.unpack('BBBBHHHHHHHH', rawdata)
        sensors = Sensors()
        sensors.set(rawdata)
        return sensors
    
    def disconnect(self):
        if self.periph is not None:
            self.periph.disconnect()
            self.periph = None
            self.curr_val_char = None


# =====================================
# Values for colorizing terminal output
# =====================================

COLOR_WARNING = '\033[93m'
COLOR_ALERT   = '\033[91m'
COLOR_OK      = '\033[92m'
COLOR_END     = '\033[0m'


# ===================================
# Class Sensor and sensor definitions
# ===================================

NUMBER_OF_SENSORS               = 7
SENSOR_IDX_HUMIDITY             = 0
SENSOR_IDX_RADON_SHORT_TERM_AVG = 1
SENSOR_IDX_RADON_LONG_TERM_AVG  = 2
SENSOR_IDX_TEMPERATURE          = 3
SENSOR_IDX_REL_ATM_PRESSURE     = 4
SENSOR_IDX_CO2_LVL              = 5
SENSOR_IDX_VOC_LVL              = 6

class Sensors():
    def __init__(self):
        self.sensor_version = None
        self.sensor_data    = [None]*NUMBER_OF_SENSORS
        self.sensor_units   = ["%rH", "Bq/m3", "Bq/m3", "degC", "hPa", "ppm", "ppb"]
        self.sensor_formats = ["{:.1f}", "{:.0f}", "{:.0f}", "{:.2f}", "{:.2f}", "{:.1f}", "{:.1f}"]
        self.show_colors    = [True, True, True, False, False, True, True]  # if true, show value in color         
        self.warning_levels = [60, 100, 100, 9999, 9999, 800, 250]
        self.alert_levels   = [70, 150, 150, 9999, 9999, 1000, 2000]
        self.lower_warning_levels = [30, 0, 0, 0, 0, 0, 0]
        self.lower_alert_levels   = [25, 0, 0, 0, 0, 0, 0]
        self.status_colors  = {}
    
    def set(self, rawData):
        self.sensor_version = rawData[0]
        if (self.sensor_version == 1):
            self.sensor_data[SENSOR_IDX_HUMIDITY]             = rawData[1]/2.0
            self.sensor_data[SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(rawData[4])
            self.sensor_data[SENSOR_IDX_RADON_LONG_TERM_AVG]  = self.conv2radon(rawData[5])
            self.sensor_data[SENSOR_IDX_TEMPERATURE]          = rawData[6]/100.0
            self.sensor_data[SENSOR_IDX_REL_ATM_PRESSURE]     = rawData[7]/50.0
            self.sensor_data[SENSOR_IDX_CO2_LVL]              = rawData[8]*1.0
            self.sensor_data[SENSOR_IDX_VOC_LVL]              = rawData[9]*1.0
        else:
            print ("ERROR: Unknown sensor version.\n")
            print ("GUIDE: Contact Airthings for support.\n")
            sys.exit(1)
   
    def conv2radon(self, radon_raw):
        radon = "N/A" # Either invalid measurement, or not available
        if 0 <= radon_raw <= 16383:
            radon  = radon_raw
        return radon

    def getOutputs(self):
        outputs = [''] * (1 + NUMBER_OF_SENSORS)
        self.status_colors  = {}

        # current time
        outputs[0] = datetime.datetime.now().strftime('%d %H:%M:%S')

        # sensors
        for i_sensor in range(NUMBER_OF_SENSORS):
            outputs[i_sensor + 1] = self.getOutputStr(i_sensor)
        
        return (outputs, self.status_colors)
        
    def getOutputStr(self, sensor_index):
        markers = self.getOutputColorMarkers(sensor_index)
        return markers[0] + self.getValueStr(sensor_index) + " " + str(self.getUnit(sensor_index)) + markers[1]

    def getValueStr(self, sensor_index):
        return self.sensor_formats[sensor_index].format(self.getValue(sensor_index))

    def getValue(self, sensor_index):
        return self.sensor_data[sensor_index]

    def getUnit(self, sensor_index):
        return self.sensor_units[sensor_index]

    def getOutputColorMarkers(self, sensor_index):
        if (Mode!='terminal' or not self.show_colors[sensor_index]):
            return ("", "")
        
        sensor_value = self.getValue(sensor_index)
        
        if (sensor_value >= self.alert_levels[sensor_index] or sensor_value <= self.lower_alert_levels[sensor_index]):
            self.status_colors[sensor_index] = Colors.Red()
            return (COLOR_ALERT, COLOR_END) 
        if (sensor_value >= self.warning_levels[sensor_index] or sensor_value <= self.lower_warning_levels[sensor_index]):
            self.status_colors[sensor_index] = Colors.Yellow()
            return (COLOR_WARNING, COLOR_END)
        
        self.status_colors[sensor_index] = Colors.GreenLow() # less brightness for better distinction from yellow
        return (COLOR_OK, COLOR_END)


try:
    #---- Initialize ----#
    waveplus = WavePlus(SerialNumber)
    ledController = LedController()

    if (Mode=='terminal'):
        print ("\nPress ctrl+C to exit program\n")
    
    print (f"Device serial number: {SerialNumber}")
    
    header = ['Date, time', 'Humidity', 'Radon ST avg', 'Radon LT avg', 'Temperature', 'Pressure', 'CO2 level', 'VOC level']
    COLUMN_WIDTH = 12
    
    if (Mode=='terminal'):
        print (tableprint.header(header, width=COLUMN_WIDTH))
    elif (Mode=='pipe'):
        print (header)
        
    MAX_FAILURES = 5
    failure_count = 0
    
    while True:
        ledController.OnCommsStart()
        
        try:
            waveplus.connect()
            failure_count = 0
        except:
            ledController.OnCommsEnd()
            if failure_count < MAX_FAILURES:
                failure_count += 1
                RETRY_TIME = 15
                print (f"Failed to connect, retry in {RETRY_TIME} sec")
                ledController.WaitWithCommsLedErrorBlinking(RETRY_TIME)
                continue

            print (f"Too many failures ({failure_count}), exiting")
            break
        
        ledController.OnCommsEnd()

        # read values
        sensors = waveplus.read()

        # get formatted output
        data, status_colors = sensors.getOutputs()
        
        if (Mode=='terminal'):
            print (tableprint.row(data, width=COLUMN_WIDTH))
        elif (Mode=='pipe'):
            print (data)

        # show status colors of these sensors
        colors = [()] * 3
        colors[0] = status_colors[SENSOR_IDX_HUMIDITY]
        colors[1] = status_colors[SENSOR_IDX_CO2_LVL]
        colors[2] = status_colors[SENSOR_IDX_VOC_LVL]
        ledController.ShowStatusLeds(colors)
        
        waveplus.disconnect()

        ledController.WaitWithCommsLedGoodStateBlinking(SamplePeriod)
            
finally:
    print ("Disconnecting")
    ledController.OnDisconnect()
    waveplus.disconnect()
    ledController.OnEndProgram()
