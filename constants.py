#!/usr/bin/env python

# Global Variables
BYTEMASK = 0xff
FUNC_READ = 0
FUNC_WRITE = 1
RW_LENGTH_ALL = 0xffff

# Logging Variables
logfilename = 'events.log'

# Heatmiser Thermostat Global Variables
hmMasterAddress = 0x81
hmMAXStats = 32
hmStatList = [1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 14]
hmThermostats = {}

# Setting for the MQTT element of the service
hmMQTTpath = "ourHome/Heatmiser"
MQTTBrokerIP = '192.168.0.65'
MQTTBrokerPort = 1883

# Settings for the Serial interface element to the Thermostats
hmSerialIP = '192.168.0.9'
hmSerialPort = 1023
hmSerialTimeout = 1

# Heatmiser DCB Function list
# Format [ID],  0 = DCBUniqueAddress,
#               1 = DCBFunctionName,
#               2 = Bytes,
#               3 = Include in Outbound MQTT Messages,
#               4 = Offset for Read from Frame
#               5 = Read/Write,
#               6 = MinValue expected (0 where RO),
#               7 = MaxValue expected (0 where RO)
hmDCBStructure = dict()
hmDCBStructure[0] = [2, 'VendorID', 1, 0, 9, 'RO', 0, 0]            # 0 = Heatmiser, 1 = OEM
hmDCBStructure[1] = [4, 'ModelType', 1, 0, 9, 'RO', 0, 0]           # 0 = DT, 1 = DT-E, 2 = PRT, 3 = PRT-E, 4 = PRTHW
hmDCBStructure[2] = [5, 'TempFormat', 1, 0, 9, 'RO', 0, 0]          # 0 = C, 1 = F
hmDCBStructure[3] = [7, 'FrostProtect', 1, 1, 9, 'RO', 0, 0]        # 0 = Off, 1 = On
hmDCBStructure[4] = [11, 'StatAddress', 1, 0, 9, 'RO', 1, 0]        # In Range 1 to 32
hmDCBStructure[5] = [16, 'ProgramMode', 1, 0, 9, 'RO', 0, 0]        # 0 = 5/2 day mode, 1 = 7 day mode
hmDCBStructure[6] = [17, 'FrostTemp', 1, 1, 9, 'RW', 7, 17]         # Frost Temp in range 7 to 17
hmDCBStructure[7] = [18, 'SetTemp', 1, 1, 9, 'RW', 5, 35]           # Room Temp setting in range 5 to 35
hmDCBStructure[8] = [19, 'FloorMax', 1, 0, 9, 'RW', 20, 45]         # Max Floor Temp in range 20 to 45
hmDCBStructure[9] = [20, 'FloorProtect', 1, 0, 9, 'RW', 0, 1]       # Max Floor Temp enable 0 = Off, 1 = On
hmDCBStructure[10] = [21, 'OnOffState', 1, 1, 9, 'RW', 0, 1]        # 0 = Off, 1 = On
hmDCBStructure[11] = [22, 'KeyLockState', 1, 0, 9, 'RW', 0, 1]      # 0 = Off, 1 = On
hmDCBStructure[12] = [23, 'RunMode', 1, 1, 9, 'RW', 0, 1]           # 0 = Heating Mode, 1 = Frost Protection Mode
hmDCBStructure[13] = [24, 'HolidayTime', 2, 1, 9, 'RW', 0, 99]      # Holiday Hours (2 Byte value)(expect to receive value in days from MQTT)
hmDCBStructure[14] = [38, 'StatTemp', 2, 1, 3, 'RO', 0, 0]          # Room Temp
hmDCBStructure[15] = [40, 'ErrorCode', 1, 1, 3, 'RO', 0, 0]         # 0 = air sensor error, 1 = floor sensor error, 2 = remote air sensor error
hmDCBStructure[16] = [41, 'HeatingState', 1, 1, 3, 'RO', 0, 0]      # 0 = Off, 1 = On
hmDCBStructure[17] = [42, 'WaterState', 1, 1 ,3, 'RW', 0, 1]	    # 0 = Off, 1 = On
hmDCBStructure[18] = [43, 'DayofWeek', 1, 0 ,3, 'RW', 0, 7]         # 1-7, Mon-Sun
hmDCBStructure[19] = [44, 'Hour', 1, 0 ,3, 'RW', 0, 23]             # 0 to 23
hmDCBStructure[20] = [45, 'Minutes', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59
hmDCBStructure[21] = [46, 'Seconds', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59
