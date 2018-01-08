#!/usr/bin/env python
import Queue
import tweepy

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

# Settings for Twitter
twConsumerKey = '<your key>'
twConsumerSecret = ',your secret>'
twAccessToken = '<your access token>'
twAccessTokenSecret = '<your access token secret>'
twAuth = tweepy.OAuthHandler(twConsumerKey, twConsumerSecret)
twAuth.set_access_token(twAccessToken, twAccessTokenSecret)

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
hmDCBStructure[0] = [2, 'VendorID', 1, 0, 9, 'RO', 0, 0]                        # 0 = Heatmiser, 1 = OEM
hmDCBStructure[1] = [4, 'ModelType', 1, 0, 9, 'RO', 0, 0]                       # 0 = DT, 1 = DT-E, 2 = PRT, 3 = PRT-E, 4 = PRTHW
hmDCBStructure[2] = [5, 'TempFormat', 1, 0, 9, 'RO', 0, 0]                      # 0 = C, 1 = F
hmDCBStructure[3] = [6, 'SwitchDiff', 1, 1, 9, 'RO', 0, 0]                      # Switching differential from 0.5 to 3 degrees
hmDCBStructure[4] = [7, 'FrostProtect', 1, 1, 9, 'RO', 0, 0]                    # 0 = Off, 1 = On
hmDCBStructure[5] = [8, 'CalibOffset', 2, 0, 9, 'RO', 0, 0]                     # Callibration Offset
hmDCBStructure[6] = [10, 'OutputDelay', 1, 0, 9, 'RO', 0, 0]                    # Output Delay 0 to 15 minutes
hmDCBStructure[7] = [11, 'StatAddress', 1, 0, 9, 'RO', 0, 0]                    # In Range 1 to 32
hmDCBStructure[8] = [12, 'KeyLimit', 1, 0, 9, 'RO', 0, 0]                       # Up/Down Temperature Limit 0 to 10 degrees
hmDCBStructure[9] = [13, 'SensorSelect', 1, 0, 9, 'RO', 0, 0]                   # Sensor selection 0 = Built-in air, 1 = Remote air, 2 = Floor, 3 = Built-in air + Floor, 4 = Remote air + Floor
hmDCBStructure[10] = [14, 'OptimumStart', 1, 0, 9, 'RO', 0, 0]                  # Optimum Start 0 = Disable, 1 = 1hr, 2 = 2hr, 3 = 3hr
hmDCBStructure[11] = [15, 'RateChange', 1, 0, 9, 'RO', 0, 0]                    # Rate of Change 
hmDCBStructure[12] = [16, 'ProgramMode', 1, 0, 9, 'RO', 0, 0]                   # 0 = 5/2 day mode, 1 = 7 day mode
hmDCBStructure[13] = [17, 'FrostTemp', 1, 1, 9, 'RW', 7, 17]                    # Frost Temp in range 7 to 17
hmDCBStructure[14] = [18, 'SetTemp', 1, 1, 9, 'RW', 5, 35]                      # Room Temp setting in range 5 to 35
hmDCBStructure[15] = [19, 'FloorMax', 1, 0, 9, 'RW', 20, 45]                    # Max Floor Temp in range 20 to 45
hmDCBStructure[16] = [20, 'FloorProtect', 1, 0, 9, 'RW', 0, 1]                  # Max Floor Temp enable 0 = Off, 1 = On
hmDCBStructure[17] = [21, 'OnOffState', 1, 1, 9, 'RW', 0, 1]                    # 0 = Off, 1 = On
hmDCBStructure[18] = [22, 'KeyLockState', 1, 1, 9, 'RW', 0, 1]                  # 0 = Off, 1 = On
hmDCBStructure[19] = [23, 'RunMode', 1, 1, 9, 'RW', 0, 1]                       # 0 = Heating Mode, 1 = Frost Protection Mode
hmDCBStructure[20] = [24, 'HolidayTime', 2, 1, 9, 'RW', 0, 99]                  # Holiday Hours (2 Byte value)(high byte, low byte for receive, reverse for send)(expect to receive value in days from MQTT)
hmDCBStructure[21] = [32, 'HoldTime', 2, 1, 3, 'RO', 0, 0]                      # Hold Time in minutes (2 Byte value)
hmDCBStructure[22] = [34, 'RemoteAir', 2, 1, 3, 'RO', 0, 0]                     # Remote Air Sensor Temp
hmDCBStructure[23] = [36, 'FloorTemp', 2, 1, 3, 'RO', 0, 0]                     # Floor Sensor Temp
hmDCBStructure[24] = [38, 'StatTemp', 2, 1, 3, 'RO', 0, 0]                      # Built-in Air Sensor Temp
hmDCBStructure[25] = [40, 'ErrorCode', 1, 1, 3, 'RO', 0, 0]                     # 0 = air sensor error, 1 = floor sensor error, 2 = remote air sensor error
hmDCBStructure[26] = [41, 'HeatingState', 1, 1, 3, 'RO', 0, 0]                  # 0 = Off, 1 = On
hmDCBStructure[27] = [42, 'WaterState', 1, 1, 3, 'RW', 0, 1]                    # 0 = Off, 1 = On
hmDCBStructure[28] = [43, 'DayofWeek', 1, 0, 3, 'RO', 0, 7]                     # 1-7, Mon-Sun
hmDCBStructure[29] = [44, 'Hour', 1, 0, 3, 'RO', 0, 23]                         # 0 to 23
hmDCBStructure[30] = [45, 'Minutes', 1, 0, 3, 'RO', 0, 59]                      # 0 to 59
hmDCBStructure[31] = [46, 'Seconds', 1, 0, 3, 'RO', 0, 59]                      # 0 to 59
hmDCBStructure[32] = [47, 'Weekday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[33] = [48, 'Weekday:Time1:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[34] = [49, 'Weekday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[35] = [50, 'Weekday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[36] = [51, 'Weekday:Time2:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[37] = [52, 'Weekday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[38] = [53, 'Weekday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[39] = [54, 'Weekday:Time3:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[40] = [55, 'Weekday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[41] = [56, 'Weekday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[42] = [57, 'Weekday:Time4:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[43] = [58, 'Weekday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[44] = [59, 'Weekend:Time1:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[45] = [60, 'Weekend:Time1:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[46] = [61, 'Weekend:Time1:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[47] = [62, 'Weekend:Time2:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[48] = [63, 'Weekend:Time2:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[49] = [64, 'Weekend:Time2:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[50] = [65, 'Weekend:Time3:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[51] = [66, 'Weekend:Time3:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[52] = [67, 'Weekend:Time3:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[53] = [68, 'Weekend:Time4:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[54] = [69, 'Weekend:Time4:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[55] = [70, 'Weekend:Time4:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[56] = [71, 'Weekday:Time1:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[57] = [72, 'Weekday:Time1:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[58] = [73, 'Weekday:Time1:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[59] = [74, 'Weekday:Time1:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[60] = [75, 'Weekday:Time2:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[61] = [76, 'Weekday:Time2:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[62] = [77, 'Weekday:Time2:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[63] = [78, 'Weekday:Time2:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[64] = [79, 'Weekday:Time3:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[65] = [80, 'Weekday:Time3:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[66] = [81, 'Weekday:Time3:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[67] = [82, 'Weekday:Time3:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[68] = [83, 'Weekday:Time4:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[69] = [84, 'Weekday:Time4:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[70] = [85, 'Weekday:Time4:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[71] = [86, 'Weekday:Time4:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[72] = [87, 'Weekend:Time1:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[73] = [88, 'Weekend:Time1:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[74] = [89, 'Weekend:Time1:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[75] = [90, 'Weekend:Time1:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[76] = [91, 'Weekend:Time2:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[77] = [92, 'Weekend:Time2:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[78] = [93, 'Weekend:Time2:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[79] = [94, 'Weekend:Time2:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[80] = [95, 'Weekend:Time3:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[81] = [96, 'Weekend:Time3:ON:Min', 1, 0, 3, 'RO', 0, 59]         # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[82] = [97, 'Weekend:Time3:OFF:Hour', 1, 0, 3, 'RO', 0, 23]       # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[83] = [98, 'Weekend:Time3:OFF:Min', 1, 0, 3, 'RO', 0, 59]        # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[84] = [99, 'Weekend:Time4:ON:Hour', 1, 0, 3, 'RO', 0, 23]        # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[85] = [100, 'Weekend:Time4:ON:Min', 1, 0, 3, 'RO', 0, 59]        # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[86] = [101, 'Weekend:Time4:OFF:Hour', 1, 0, 3, 'RO', 0, 23]      # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[87] = [102, 'Weekend:Time4:OFF:Min', 1, 0, 3, 'RO', 0, 59]       # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[88] = [103, 'Monday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[89] = [104, 'Monday:Time1:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[90] = [105, 'Monday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[91] = [106, 'Monday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[92] = [107, 'Monday:Time2:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[93] = [108, 'Monday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[94] = [109, 'Monday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[95] = [110, 'Monday:Time3:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[96] = [111, 'Monday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[97] = [112, 'Monday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]           # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[98] = [113, 'Monday:Time4:Min', 1, 0, 3, 'RO', 0, 59]            # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[99] = [114, 'Monday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]           # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[100] = [115, 'Tuesday:Time1:Hour', 1, 0 ,3, 'RO', 0, 23]         # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[101] = [116, 'Tuesday:Time1:Min', 1, 0, 3, 'RO', 0, 59]          # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[102] = [117, 'Tuesday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]         # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[103] = [118, 'Tuesday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]         # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[104] = [119, 'Tuesday:Time2:Min', 1, 0, 3, 'RO', 0, 59]          # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[105] = [120, 'Tuesday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]         # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[106] = [121, 'Tuesday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]         # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[107] = [122, 'Tuesday:Time3:Min', 1, 0, 3, 'RO', 0, 59]          # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[108] = [123, 'Tuesday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]         # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[109] = [124, 'Tuesday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]         # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[110] = [125, 'Tuesday:Time4:Min', 1, 0, 3, 'RO', 0, 59]          # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[111] = [126, 'Tuesday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]         # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[112] = [127, 'Wednesday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]       # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[113] = [128, 'Wednesday:Time1:Min', 1, 0, 3, 'RO', 0, 59]        # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[114] = [129, 'Wednesday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]       # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[115] = [130, 'Wednesday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]       # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[116] = [131, 'Wednesday:Time2:Min', 1, 0, 3, 'RO', 0, 59]        # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[117] = [132, 'Wednesday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]       # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[118] = [133, 'Wednesday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]       # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[119] = [134, 'Wednesday:Time3:Min', 1, 0, 3, 'RO', 0, 59]        # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[120] = [135, 'Wednesday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]       # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[121] = [136, 'Wednesday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]       # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[122] = [137, 'Wednesday:Time4:Min', 1, 0, 3, 'RO', 0, 59]        # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[123] = [138, 'Wednesday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]       # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[124] = [139, 'Thursday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[125] = [140, 'Thursday:Time1:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[126] = [141, 'Thursday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[127] = [142, 'Thursday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[128] = [143, 'Thursday:Time2:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[129] = [144, 'Thursday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[130] = [145, 'Thursday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[131] = [146, 'Thursday:Time3:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[132] = [147, 'Thursday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[133] = [148, 'Thursday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[134] = [149, 'Thursday:Time4:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[135] = [150, 'Thursday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[136] = [151, 'Friday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[137] = [152, 'Friday:Time1:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[138] = [153, 'Friday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[139] = [154, 'Friday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[140] = [155, 'Friday:Time2:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[141] = [156, 'Friday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[142] = [157, 'Friday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[143] = [158, 'Friday:Time3:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[144] = [159, 'Friday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[145] = [160, 'Friday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[146] = [161, 'Friday:Time4:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[147] = [162, 'Friday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[148] = [163, 'Saturday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[149] = [164, 'Saturday:Time1:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[150] = [165, 'Saturday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[151] = [166, 'Saturday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[152] = [167, 'Saturday:Time2:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[153] = [168, 'Saturday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[154] = [169, 'Saturday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[155] = [170, 'Saturday:Time3:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[156] = [171, 'Saturday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[157] = [172, 'Saturday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]        # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[158] = [173, 'Saturday:Time4:Min', 1, 0, 3, 'RO', 0, 59]         # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[159] = [174, 'Saturday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]        # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[160] = [175, 'Sunday:Time1:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 1, range 0 to 23
hmDCBStructure[161] = [176, 'Sunday:Time1:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 1, range 0 to 59
hmDCBStructure[162] = [177, 'Sunday:Time1:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 1, range 5 to 35
hmDCBStructure[163] = [178, 'Sunday:Time2:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 2, range 0 to 23
hmDCBStructure[164] = [179, 'Sunday:Time2:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 2, range 0 to 59
hmDCBStructure[165] = [180, 'Sunday:Time2:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 2, range 5 to 35
hmDCBStructure[166] = [181, 'Sunday:Time3:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 3, range 0 to 23
hmDCBStructure[167] = [182, 'Sunday:Time3:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 3, range 0 to 59
hmDCBStructure[168] = [183, 'Sunday:Time3:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 3, range 5 to 35
hmDCBStructure[169] = [184, 'Sunday:Time4:Hour', 1, 0, 3, 'RO', 0, 23]          # Start Hour for Timer 4, range 0 to 23
hmDCBStructure[170] = [185, 'Sunday:Time4:Min', 1, 0, 3, 'RO', 0, 59]           # Start Minute for Timer 4, range 0 to 59
hmDCBStructure[171] = [186, 'Sunday:Time4:Temp', 1, 0, 3, 'RO', 0, 35]          # Target temperature for Timer 4, range 5 to 35
hmDCBStructure[172] = [187, 'Monday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[173] = [188, 'Monday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[174] = [189, 'Monday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[175] = [190, 'Monday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[176] = [191, 'Monday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[177] = [192, 'Monday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[178] = [193, 'Monday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[179] = [194, 'Monday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[180] = [195, 'Monday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[181] = [196, 'Monday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[182] = [197, 'Monday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[183] = [198, 'Monday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[184] = [199, 'Monday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[185] = [200, 'Monday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[186] = [201, 'Monday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[187] = [202, 'Monday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[188] = [203, 'Tuesday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]      # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[190] = [204, 'Tuesday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]       # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[191] = [205, 'Tuesday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]     # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[192] = [206, 'Tuesday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]      # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[193] = [207, 'Tuesday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]      # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[194] = [208, 'Tuesday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]       # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[195] = [209, 'Tuesday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]     # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[196] = [210, 'Tuesday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]      # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[197] = [211, 'Tuesday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]      # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[198] = [212, 'Tuesday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]       # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[199] = [213, 'Tuesday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]     # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[200] = [214, 'Tuesday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]      # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[201] = [215, 'Tuesday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]      # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[202] = [216, 'Tuesday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]       # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[203] = [217, 'Tuesday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]     # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[204] = [218, 'Tuesday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]      # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[205] = [219, 'Wednesday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]    # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[206] = [220, 'Wednesday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]     # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[207] = [221, 'Wednesday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]   # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[208] = [222, 'Wednesday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]    # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[209] = [223, 'Wednesday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]    # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[210] = [224, 'Wednesday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]     # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[211] = [225, 'Wednesday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]   # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[212] = [226, 'Wednesday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]    # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[213] = [227, 'Wednesday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]    # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[214] = [228, 'Wednesday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]     # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[215] = [229, 'Wednesday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]   # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[216] = [230, 'Wednesday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]    # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[217] = [231, 'Wednesday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]    # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[218] = [232, 'Wednesday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]     # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[219] = [233, 'Wednesday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]   # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[220] = [234, 'Wednesday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]    # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[221] = [235, 'Thursday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[222] = [236, 'Thursday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[223] = [237, 'Thursday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[224] = [238, 'Thursday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[225] = [239, 'Thursday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[226] = [240, 'Thursday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[227] = [241, 'Thursday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[228] = [242, 'Thursday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[229] = [243, 'Thursday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[230] = [244, 'Thursday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[231] = [245, 'Thursday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[232] = [246, 'Thursday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[233] = [247, 'Thursday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[234] = [248, 'Thursday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[235] = [249, 'Thursday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[236] = [250, 'Thursday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[237] = [251, 'Friday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[238] = [252, 'Friday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[239] = [253, 'Friday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[240] = [254, 'Friday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[241] = [255, 'Friday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[242] = [256, 'Friday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[243] = [257, 'Friday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[244] = [258, 'Friday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[245] = [259, 'Friday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[246] = [260, 'Friday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[247] = [261, 'Friday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[248] = [262, 'Friday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[249] = [263, 'Friday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[250] = [264, 'Friday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[251] = [265, 'Friday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[252] = [266, 'Friday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[253] = [267, 'Saturday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[254] = [268, 'Saturday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[255] = [269, 'Saturday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[256] = [270, 'Saturday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[257] = [271, 'Saturday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[258] = [272, 'Saturday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[259] = [273, 'Saturday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[260] = [274, 'Saturday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[261] = [275, 'Saturday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[262] = [276, 'Saturday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[263] = [277, 'Saturday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[264] = [278, 'Saturday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[265] = [279, 'Saturday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]     # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[266] = [280, 'Saturday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]      # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[267] = [281, 'Saturday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]    # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[268] = [282, 'Saturday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]     # OFF Minute for Timer 4, range 0 to 59
hmDCBStructure[269] = [283, 'Sunday:Time1:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 1, range 0 to 23
hmDCBStructure[270] = [284, 'Sunday:Time1:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 1, range 0 to 59
hmDCBStructure[271] = [285, 'Sunday:Time1:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 1, range 0 to 23
hmDCBStructure[272] = [286, 'Sunday:Time1:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 1, range 0 to 59
hmDCBStructure[273] = [287, 'Sunday:Time2:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 2, range 0 to 23
hmDCBStructure[274] = [288, 'Sunday:Time2:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 2, range 0 to 59
hmDCBStructure[275] = [289, 'Sunday:Time2:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 2, range 0 to 23
hmDCBStructure[276] = [290, 'Sunday:Time2:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 2, range 0 to 59
hmDCBStructure[277] = [291, 'Sunday:Time3:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 3, range 0 to 23
hmDCBStructure[278] = [292, 'Sunday:Time3:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 3, range 0 to 59
hmDCBStructure[279] = [293, 'Sunday:Time3:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 3, range 0 to 23
hmDCBStructure[280] = [294, 'Sunday:Time3:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 3, range 0 to 59
hmDCBStructure[281] = [295, 'Sunday:Time4:ON:Hour', 1, 0 ,3, 'RO', 0, 23]       # ON Hour for Timer 4, range 0 to 23
hmDCBStructure[282] = [296, 'Sunday:Time4:ON:Min', 1, 0 ,3, 'RO', 0, 59]        # ON Minute for Timer 4, range 0 to 59
hmDCBStructure[283] = [297, 'Sunday:Time4:OFF:Hour', 1, 0 ,3, 'RO', 0, 23]      # OFF Hour for Timer 4, range 0 to 23
hmDCBStructure[284] = [298, 'Sunday:Time4:OFF:Min', 1, 0 ,3, 'RO', 0, 59]       # OFF Minute for Timer 4, range 0 to 59
