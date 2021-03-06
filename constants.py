#!/usr/bin/env python

# Global Variables
BYTEMASK = 0xff
FUNC_READ = 0
FUNC_WRITE = 1
RW_LENGTH_ALL = 0xffff
hmPollCycle = 2                                                     # Polling interval for status updates from Stats

# Logging Variables
logfilename = 'events.log'                                          # Log file name

# Heatmiser Thermostat Global Variables
hmMasterAddress = 0x81                                              # Can be either 0x81 or 0xa0
hmMAXStats = 32                                                     # Max number of Stats available on 1 system
hmStatList = [1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 14]                  # List of the Stat ID's used
hmThermostats = {}                                                  # Dynamic array to hold current thermostat status

# Setting for the MQTT element of the service
hmMQTTpath = "<your MQTT Subscription Path>"                        # Subscription path used for your MQTT Broker   
MQTTBrokerIP = 'MQTT Broker IP'                                     # IP Address of the MQTT Broker
MQTTBrokerPort = 1883                                               # IP Port number of the MQTT Broker

# Settings for the Serial interface element to the Thermostats
hmSerialIP = 'Serial Interface IP Address'                          # IP Address for the serial interface (IP to RS485)
hmSerialPort = 1023                                                 # IP Port number for the serial interface
hmSerialTimeout = 1

# Heatmiser DCB Function list
# Full details of all functions can be found in the Heatmiser v3 Protocol document
# Settings below match those within the protocol description for RO and RW options
# Format [ID],  0 = DCBUniqueAddress,
#               1 = DCBFunctionName,
#               2 = Bytes,
#               3 = Include in Outbound MQTT Messages,
#               4 = Offset for Read from Frame
#               5 = Read/Write (used to determine whether to monitor the MQTT broker for chnage),
#               6 = MinValue expected (0 where RO),
#               7 = MaxValue expected (0 where RO)
hmDCBStructure = dict()
hmDCBStructure[0] = [2, 'VendorID', 1, 0, 9, 'RO', 0, 0]            # 0 = Heatmiser, 1 = OEM
hmDCBStructure[1] = [4, 'ModelType', 1, 0, 9, 'RO', 0, 0]           # 0 = DT, 1 = DT-E, 2 = PRT, 3 = PRT-E, 4 = PRTHW
hmDCBStructure[2] = [5, 'TempFormat', 1, 0, 9, 'RO', 0, 0]          # 0 = C, 1 = F
hmDCBStructure[3] = [6, 'SwitchDiff', 1, 0, 9, 'RO', 0, 0]          # Switching differential from 0.5 to 3 degrees
hmDCBStructure[4] = [7, 'FrostProtect', 1, 1, 9, 'RO', 0, 0]        # 0 = Off, 1 = On
hmDCBStructure[5] = [10, 'OutputDelay', 1, 0, 9, 'RO', 0, 0]        # Output Delay 0 to 15 minutes
hmDCBStructure[6] = [11, 'StatAddress', 1, 0, 9, 'RO', 0, 0]        # In Range 1 to 32
hmDCBStructure[7] = [12, 'KeyLimit', 1, 0, 9, 'RO', 0, 0]           # Up/Down Temperature Limit 0 to 10 degrees
hmDCBStructure[8] = [13, 'SensorSelect', 1, 0, 9, 'RO', 0, 0]       # Sensor selection 0 = Built-in air, 1 = Remote air, 2 = Floor, 3 = Built-in air + Floor, 4 = Remote air + Floor
hmDCBStructure[9] = [14, 'OptimumStart', 1, 0, 9, 'RO', 0, 0]       # Optimum Start 0 = Disable, 1 = 1hr, 2 = 2hr, 3 = 3hr
hmDCBStructure[10] = [15, 'RateChange', 1, 0, 9, 'RO', 0, 0]        # Rate of Change 
hmDCBStructure[11] = [16, 'ProgramMode', 1, 0, 9, 'RO', 0, 0]       # 0 = 5/2 day mode, 1 = 7 day mode
hmDCBStructure[12] = [17, 'FrostTemp', 1, 1, 9, 'RW', 7, 17]        # Frost Temp in range 7 to 17
hmDCBStructure[13] = [18, 'SetTemp', 1, 1, 9, 'RW', 5, 35]          # Room Temp setting in range 5 to 35
hmDCBStructure[14] = [19, 'FloorMax', 1, 0, 9, 'RW', 20, 45]        # Max Floor Temp in range 20 to 45
hmDCBStructure[15] = [20, 'FloorProtect', 1, 0, 9, 'RW', 0, 1]      # Max Floor Temp enable 0 = Off, 1 = On
hmDCBStructure[16] = [21, 'OnOffState', 1, 1, 9, 'RW', 0, 1]        # 0 = Off, 1 = On
hmDCBStructure[17] = [22, 'KeyLockState', 1, 0, 9, 'RW', 0, 1]      # 0 = Off, 1 = On
hmDCBStructure[18] = [23, 'RunMode', 1, 1, 9, 'RW', 0, 1]           # 0 = Heating Mode, 1 = Frost Protection Mode
hmDCBStructure[19] = [24, 'HolidayTime', 2, 1, 9, 'RW', 0, 99]      # Holiday Hours (2 Byte value)(high byte, low byte for receive, reverse for send)(expect to receive value in days from MQTT)
hmDCBStructure[20] = [32, 'HoldTime', 2, 1, 3, 'RO', 0, 0]          # Hold Time in minutes (2 Byte value)
hmDCBStructure[21] = [34, 'RemoteAir', 2, 1, 3, 'RO', 0, 0]         # Remote Air Sensor Temp
hmDCBStructure[22] = [36, 'FloorTemp', 2, 1, 3, 'RO', 0, 0]         # Floor Sensor Temp
hmDCBStructure[23] = [38, 'StatTemp', 2, 1, 3, 'RO', 0, 0]          # Built-in Air Sensor Temp
hmDCBStructure[24] = [40, 'ErrorCode', 1, 1, 3, 'RO', 0, 0]         # 0 = air sensor error, 1 = floor sensor error, 2 = remote air sensor error
hmDCBStructure[25] = [41, 'HeatingState', 1, 1, 3, 'RO', 0, 0]      # 0 = Off, 1 = On
hmDCBStructure[26] = [42, 'WaterState', 1, 1 ,3, 'RW', 0, 1]	      # 0 = Off, 1 = On
hmDCBStructure[27] = [43, 'DayofWeek', 1, 0 ,3, 'RW', 0, 7]         # 1-7, Mon-Sun
hmDCBStructure[28] = [44, 'Hour', 1, 0 ,3, 'RW', 0, 23]             # 0 to 23
hmDCBStructure[29] = [45, 'Minutes', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59
hmDCBStructure[30] = [46, 'Seconds', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59
