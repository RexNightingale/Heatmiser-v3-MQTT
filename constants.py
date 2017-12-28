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
xmlfilename = 'heatmiserconfig.xml'                                 # XML configuration file name

# Heatmiser Thermostat Global Variables
hmMasterAddress = 0x81                                              # Can be either 0x81 or 0xa0
hmMAXStats = 32                                                     # Max number of Stats available on 1 system
hmStatList = [1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 14]                  # List of the Stat ID's used
hmThermostats = {}                                                  # Dynamic array to hold current thermostat status
hmThermostatTimers = {}

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
hmDCBStructure[26] = [42, 'WaterState', 1, 1 ,3, 'RW', 0, 1]        # 0 = Off, 1 = On
hmDCBStructure[27] = [43, 'DayofWeek', 1, 0 ,3, 'RW', 0, 7]         # 1-7, Mon-Sun
hmDCBStructure[28] = [44, 'Hour', 1, 0 ,3, 'RW', 0, 23]             # 0 to 23
hmDCBStructure[29] = [45, 'Minutes', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59
hmDCBStructure[30] = [46, 'Seconds', 1, 0 ,3, 'RW', 0, 59]          # 0 to 59

# Heatmiser DCB Timers list
# Full details of all functions can be found in the Heatmiser v3 Protocol document
# Settings below match those within the timers sections of the thermostats
# Format [ID],  0 = DCBUniqueAddress,
#               1 = Day of week (7 day timers, Weekday/Weekend for 5/2 timers),
#               2 = Time block,
#               3 = ON / OFF definition for on/off timer functions only.  '' where not applicable,
#               4 = Hour, Minute or Temp value definition
hmDCBTimers = dict()
hmDCBTimers[0] = [49, 'Weekday', 'Time1', '', 'Hour']
hmDCBTimers[1] = [50, 'Weekday', 'Time1', '', 'Minute']
hmDCBTimers[2] = [51, 'Weekday', 'Time1', '', 'Temp']
hmDCBTimers[3] = [52, 'Weekday', 'Time2', '', 'Hour']
hmDCBTimers[4] = [53, 'Weekday', 'Time2', '', 'Minute']
hmDCBTimers[5] = [54, 'Weekday', 'Time2', '', 'Temp']
hmDCBTimers[6] = [55, 'Weekday', 'Time3', '', 'Hour']
hmDCBTimers[7] = [56, 'Weekday', 'Time3', '', 'Minute']
hmDCBTimers[8] = [57, 'Weekday', 'Time3', '', 'Temp']
hmDCBTimers[9] = [58, 'Weekday', 'Time4', '', 'Hour']
hmDCBTimers[10] = [59, 'Weekday', 'Time4', '', 'Minute']
hmDCBTimers[11] = [60, 'Weekday', 'Time4', '', 'Temp']
hmDCBTimers[12] = [61, 'Weekend', 'Time1', '', 'Hour']
hmDCBTimers[13] = [62, 'Weekend', 'Time1', '', 'Minute']
hmDCBTimers[14] = [63, 'Weekend', 'Time1', '', 'Temp']
hmDCBTimers[15] = [64, 'Weekend', 'Time2', '', 'Hour']
hmDCBTimers[16] = [65, 'Weekend', 'Time2', '', 'Minute']
hmDCBTimers[17] = [66, 'Weekend', 'Time2', '', 'Temp']
hmDCBTimers[18] = [67, 'Weekend', 'Time3', '', 'Hour']
hmDCBTimers[19] = [68, 'Weekend', 'Time3', '', 'Minute']
hmDCBTimers[20] = [69, 'Weekend', 'Time3', '', 'Temp']
hmDCBTimers[21] = [70, 'Weekend', 'Time4', '', 'Hour']
hmDCBTimers[22] = [71, 'Weekend', 'Time4', '', 'Minute']
hmDCBTimers[23] = [72, 'Weekend', 'Time4', '', 'Temp']
hmDCBTimers[24] = [72, 'Weekday', 'Time1', 'ON', 'Hour']
hmDCBTimers[25] = [73, 'Weekday', 'Time1', 'ON', 'Minute']
hmDCBTimers[26] = [74, 'Weekday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[27] = [75, 'Weekday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[28] = [76, 'Weekday', 'Time2', 'ON', 'Hour']
hmDCBTimers[29] = [77, 'Weekday', 'Time2', 'ON', 'Minute']
hmDCBTimers[30] = [78, 'Weekday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[31] = [79, 'Weekday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[32] = [80, 'Weekday', 'Time3', 'ON', 'Hour']
hmDCBTimers[33] = [81, 'Weekday', 'Time3', 'ON', 'Minute']
hmDCBTimers[34] = [82, 'Weekday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[35] = [83, 'Weekday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[36] = [84, 'Weekday', 'Time4', 'ON', 'Hour']
hmDCBTimers[37] = [85, 'Weekday', 'Time4', 'ON', 'Minute']
hmDCBTimers[38] = [86, 'Weekday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[39] = [87, 'Weekday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[40] = [88, 'Weekend', 'Time1', 'ON', 'Hour']
hmDCBTimers[41] = [89, 'Weekend', 'Time1', 'ON', 'Minute']
hmDCBTimers[42] = [90, 'Weekend', 'Time1', 'OFF', 'Hour']
hmDCBTimers[43] = [91, 'Weekend', 'Time1', 'OFF', 'Minute']
hmDCBTimers[44] = [92, 'Weekend', 'Time2', 'ON', 'Hour']
hmDCBTimers[45] = [93, 'Weekend', 'Time2', 'ON', 'Minute']
hmDCBTimers[46] = [94, 'Weekend', 'Time2', 'OFF', 'Hour']
hmDCBTimers[47] = [95, 'Weekend', 'Time2', 'OFF', 'Minute']
hmDCBTimers[48] = [96, 'Weekend', 'Time3', 'ON', 'Hour']
hmDCBTimers[49] = [97, 'Weekend', 'Time3', 'ON', 'Minute']
hmDCBTimers[50] = [98, 'Weekend', 'Time3', 'OFF', 'Hour']
hmDCBTimers[51] = [99, 'Weekend', 'Time3', 'OFF', 'Minute']
hmDCBTimers[52] = [100, 'Weekend', 'Time4', 'ON', 'Hour']
hmDCBTimers[53] = [101, 'Weekend', 'Time4', 'ON', 'Minute']
hmDCBTimers[54] = [102, 'Weekend', 'Time4', 'OFF', 'Hour']
hmDCBTimers[55] = [103, 'Weekend', 'Time4', 'OFF', 'Minute']
hmDCBTimers[56] = [104, 'Monday', 'Time1', '', 'Hour']
hmDCBTimers[57] = [105, 'Monday', 'Time1', '', 'Minute']
hmDCBTimers[58] = [106, 'Monday', 'Time1', '', 'Temp']
hmDCBTimers[59] = [107, 'Monday', 'Time2', '', 'Hour']
hmDCBTimers[60] = [108, 'Monday', 'Time2', '', 'Minute']
hmDCBTimers[61] = [109, 'Monday', 'Time2', '', 'Temp']
hmDCBTimers[62] = [110, 'Monday', 'Time3', '', 'Hour']
hmDCBTimers[63] = [111, 'Monday', 'Time3', '', 'Minute']
hmDCBTimers[64] = [112, 'Monday', 'Time3', '', 'Temp']
hmDCBTimers[65] = [113, 'Monday', 'Time4', '', 'Hour']
hmDCBTimers[66] = [114, 'Monday', 'Time4', '', 'Minute']
hmDCBTimers[67] = [115, 'Monday', 'Time4', '', 'Temp']
hmDCBTimers[68] = [116, 'Tuesday', 'Time1', '', 'Hour']
hmDCBTimers[69] = [117, 'Tuesday', 'Time1', '', 'Minute']
hmDCBTimers[70] = [118, 'Tuesday', 'Time1', '', 'Temp']
hmDCBTimers[71] = [119, 'Tuesday', 'Time2', '', 'Hour']
hmDCBTimers[72] = [120, 'Tuesday', 'Time2', '', 'Minute']
hmDCBTimers[73] = [121, 'Tuesday', 'Time2', '', 'Temp']
hmDCBTimers[74] = [122, 'Tuesday', 'Time3', '', 'Hour']
hmDCBTimers[75] = [123, 'Tuesday', 'Time3', '', 'Minute']
hmDCBTimers[76] = [124, 'Tuesday', 'Time3', '', 'Temp']
hmDCBTimers[77] = [125, 'Tuesday', 'Time4', '', 'Hour']
hmDCBTimers[78] = [126, 'Tuesday', 'Time4', '', 'Minute']
hmDCBTimers[79] = [127, 'Tuesday', 'Time4', '', 'Temp']
hmDCBTimers[80] = [128, 'Wednesday', 'Time1', '', 'Hour']
hmDCBTimers[81] = [129, 'Wednesday', 'Time1', '', 'Minute']
hmDCBTimers[82] = [130, 'Wednesday', 'Time1', '', 'Temp']
hmDCBTimers[83] = [131, 'Wednesday', 'Time2', '', 'Hour']
hmDCBTimers[84] = [132, 'Wednesday', 'Time2', '', 'Minute']
hmDCBTimers[85] = [133, 'Wednesday', 'Time2', '', 'Temp']
hmDCBTimers[86] = [134, 'Wednesday', 'Time3', '', 'Hour']
hmDCBTimers[87] = [135, 'Wednesday', 'Time3', '', 'Minute']
hmDCBTimers[88] = [136, 'Wednesday', 'Time3', '', 'Temp']
hmDCBTimers[89] = [137, 'Wednesday', 'Time4', '', 'Hour']
hmDCBTimers[90] = [138, 'Wednesday', 'Time4', '', 'Minute']
hmDCBTimers[91] = [139, 'Wednesday', 'Time4', '', 'Temp']
hmDCBTimers[92] = [140, 'Thursday', 'Time1', '', 'Hour']
hmDCBTimers[93] = [141, 'Thursday', 'Time1', '', 'Minute']
hmDCBTimers[94] = [142, 'Thursday', 'Time1', '', 'Temp']
hmDCBTimers[95] = [143, 'Thursday', 'Time2', '', 'Hour']
hmDCBTimers[96] = [144, 'Thursday', 'Time2', '', 'Minute']
hmDCBTimers[97] = [145, 'Thursday', 'Time2', '', 'Temp']
hmDCBTimers[98] = [146, 'Thursday', 'Time3', '', 'Hour']
hmDCBTimers[99] = [147, 'Thursday', 'Time3', '', 'Minute']
hmDCBTimers[100] = [148, 'Thursday', 'Time3', '', 'Temp']
hmDCBTimers[101] = [149, 'Thursday', 'Time4', '', 'Hour']
hmDCBTimers[102] = [150, 'Thursday', 'Time4', '', 'Minute']
hmDCBTimers[103] = [151, 'Thursday', 'Time4', '', 'Temp']
hmDCBTimers[104] = [152, 'Friday', 'Time1', '', 'Hour']
hmDCBTimers[105] = [153, 'Friday', 'Time1', '', 'Minute']
hmDCBTimers[106] = [154, 'Friday', 'Time1', '', 'Temp']
hmDCBTimers[107] = [155, 'Friday', 'Time2', '', 'Hour']
hmDCBTimers[108] = [156, 'Friday', 'Time2', '', 'Minute']
hmDCBTimers[109] = [157, 'Friday', 'Time2', '', 'Temp']
hmDCBTimers[110] = [158, 'Friday', 'Time3', '', 'Hour']
hmDCBTimers[111] = [159, 'Friday', 'Time3', '', 'Minute']
hmDCBTimers[112] = [160, 'Friday', 'Time3', '', 'Temp']
hmDCBTimers[113] = [161, 'Friday', 'Time4', '', 'Hour']
hmDCBTimers[114] = [162, 'Friday', 'Time4', '', 'Minute']
hmDCBTimers[115] = [163, 'Friday', 'Time4', '', 'Temp']
hmDCBTimers[116] = [164, 'Saturday', 'Time1', '', 'Hour']
hmDCBTimers[117] = [165, 'Saturday', 'Time1', '', 'Minute']
hmDCBTimers[118] = [166, 'Saturday', 'Time1', '', 'Temp']
hmDCBTimers[119] = [167, 'Saturday', 'Time2', '', 'Hour']
hmDCBTimers[120] = [168, 'Saturday', 'Time2', '', 'Minute']
hmDCBTimers[121] = [169, 'Saturday', 'Time2', '', 'Temp']
hmDCBTimers[122] = [170, 'Saturday', 'Time3', '', 'Hour']
hmDCBTimers[123] = [171, 'Saturday', 'Time3', '', 'Minute']
hmDCBTimers[124] = [172, 'Saturday', 'Time3', '', 'Temp']
hmDCBTimers[125] = [173, 'Saturday', 'Time4', '', 'Hour']
hmDCBTimers[126] = [174, 'Saturday', 'Time4', '', 'Minute']
hmDCBTimers[127] = [175, 'Saturday', 'Time4', '', 'Temp']
hmDCBTimers[128] = [176, 'Sunday', 'Time1', '', 'Hour']
hmDCBTimers[129] = [177, 'Sunday', 'Time1', '', 'Minute']
hmDCBTimers[130] = [178, 'Sunday', 'Time1', '', 'Temp']
hmDCBTimers[131] = [179, 'Sunday', 'Time2', '', 'Hour']
hmDCBTimers[132] = [180, 'Sunday', 'Time2', '', 'Minute']
hmDCBTimers[133] = [181, 'Sunday', 'Time2', '', 'Temp']
hmDCBTimers[134] = [182, 'Sunday', 'Time3', '', 'Hour']
hmDCBTimers[135] = [183, 'Sunday', 'Time3', '', 'Minute']
hmDCBTimers[136] = [184, 'Sunday', 'Time3', '', 'Temp']
hmDCBTimers[137] = [185, 'Sunday', 'Time4', '', 'Hour']
hmDCBTimers[138] = [186, 'Sunday', 'Time4', '', 'Minute']
hmDCBTimers[139] = [187, 'Sunday', 'Time4', '', 'Temp']
hmDCBTimers[140] = [188, 'Monday', 'Time1', 'ON', 'Hour']
hmDCBTimers[141] = [189, 'Monday', 'Time1', 'ON', 'Minute']
hmDCBTimers[142] = [189, 'Monday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[143] = [190, 'Monday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[144] = [191, 'Monday', 'Time2', 'ON', 'Hour']
hmDCBTimers[145] = [192, 'Monday', 'Time2', 'ON', 'Minute']
hmDCBTimers[146] = [193, 'Monday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[147] = [194, 'Monday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[148] = [195, 'Monday', 'Time3', 'ON', 'Hour']
hmDCBTimers[149] = [196, 'Monday', 'Time3', 'ON', 'Minute']
hmDCBTimers[150] = [197, 'Monday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[151] = [198, 'Monday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[152] = [199, 'Monday', 'Time4', 'ON', 'Hour']
hmDCBTimers[153] = [200, 'Monday', 'Time4', 'ON', 'Minute']
hmDCBTimers[154] = [201, 'Monday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[155] = [202, 'Monday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[156] = [203, 'Tuesday', 'Time1', 'ON', 'Hour']
hmDCBTimers[157] = [204, 'Tuesday', 'Time1', 'ON', 'Minute']
hmDCBTimers[158] = [205, 'Tuesday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[159] = [206, 'Tuesday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[160] = [207, 'Tuesday', 'Time2', 'ON', 'Hour']
hmDCBTimers[161] = [208, 'Tuesday', 'Time2', 'ON', 'Minute']
hmDCBTimers[162] = [209, 'Tuesday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[163] = [210, 'Tuesday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[164] = [211, 'Tuesday', 'Time3', 'ON', 'Hour']
hmDCBTimers[165] = [212, 'Tuesday', 'Time3', 'ON', 'Minute']
hmDCBTimers[166] = [213, 'Tuesday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[167] = [214, 'Tuesday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[168] = [215, 'Tuesday', 'Time4', 'ON', 'Hour']
hmDCBTimers[169] = [216, 'Tuesday', 'Time4', 'ON', 'Minute']
hmDCBTimers[170] = [217, 'Tuesday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[171] = [218, 'Tuesday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[172] = [219, 'Wednesday', 'Time1', 'ON', 'Hour']
hmDCBTimers[173] = [220, 'Wednesday', 'Time1', 'ON', 'Minute']
hmDCBTimers[174] = [221, 'Wednesday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[175] = [222, 'Wednesday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[176] = [223, 'Wednesday', 'Time2', 'ON', 'Hour']
hmDCBTimers[177] = [224, 'Wednesday', 'Time2', 'ON', 'Minute']
hmDCBTimers[178] = [225, 'Wednesday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[179] = [226, 'Wednesday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[180] = [227, 'Wednesday', 'Time3', 'ON', 'Hour']
hmDCBTimers[181] = [228, 'Wednesday', 'Time3', 'ON', 'Minute']
hmDCBTimers[182] = [229, 'Wednesday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[183] = [230, 'Wednesday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[184] = [231, 'Wednesday', 'Time4', 'ON', 'Hour']
hmDCBTimers[185] = [232, 'Wednesday', 'Time4', 'ON', 'Minute']
hmDCBTimers[186] = [233, 'Wednesday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[187] = [234, 'Wednesday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[188] = [235, 'Thursday', 'Time1', 'ON', 'Hour']
hmDCBTimers[189] = [236, 'Thursday', 'Time1', 'ON', 'Minute']
hmDCBTimers[190] = [237, 'Thursday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[191] = [238, 'Thursday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[192] = [239, 'Thursday', 'Time2', 'ON', 'Hour']
hmDCBTimers[193] = [240, 'Thursday', 'Time2', 'ON', 'Minute']
hmDCBTimers[194] = [241, 'Thursday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[195] = [242, 'Thursday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[196] = [243, 'Thursday', 'Time3', 'ON', 'Hour']
hmDCBTimers[197] = [244, 'Thursday', 'Time3', 'ON', 'Minute']
hmDCBTimers[198] = [245, 'Thursday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[199] = [246, 'Thursday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[200] = [247, 'Thursday', 'Time4', 'ON', 'Hour']
hmDCBTimers[201] = [248, 'Thursday', 'Time4', 'ON', 'Minute']
hmDCBTimers[202] = [249, 'Thursday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[203] = [250, 'Thursday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[204] = [251, 'Friday', 'Time1', 'ON', 'Hour']
hmDCBTimers[206] = [252, 'Friday', 'Time1', 'ON', 'Minute']
hmDCBTimers[207] = [253, 'Friday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[208] = [254, 'Friday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[209] = [255, 'Friday', 'Time2', 'ON', 'Hour']
hmDCBTimers[210] = [256, 'Friday', 'Time2', 'ON', 'Minute']
hmDCBTimers[211] = [257, 'Friday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[212] = [258, 'Friday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[213] = [259, 'Friday', 'Time3', 'ON', 'Hour']
hmDCBTimers[214] = [260, 'Friday', 'Time3', 'ON', 'Minute']
hmDCBTimers[215] = [261, 'Friday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[216] = [262, 'Friday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[217] = [263, 'Friday', 'Time4', 'ON', 'Hour']
hmDCBTimers[218] = [264, 'Friday', 'Time4', 'ON', 'Minute']
hmDCBTimers[219] = [265, 'Friday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[220] = [266, 'Friday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[221] = [267, 'Saturday', 'Time1', 'ON', 'Hour']
hmDCBTimers[222] = [268, 'Saturday', 'Time1', 'ON', 'Minute']
hmDCBTimers[223] = [269, 'Saturday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[224] = [270, 'Saturday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[225] = [271, 'Saturday', 'Time2', 'ON', 'Hour']
hmDCBTimers[226] = [272, 'Saturday', 'Time2', 'ON', 'Minute']
hmDCBTimers[228] = [273, 'Saturday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[229] = [274, 'Saturday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[230] = [275, 'Saturday', 'Time3', 'ON', 'Hour']
hmDCBTimers[231] = [276, 'Saturday', 'Time3', 'ON', 'Minute']
hmDCBTimers[232] = [277, 'Saturday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[233] = [278, 'Saturday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[234] = [279, 'Saturday', 'Time4', 'ON', 'Hour']
hmDCBTimers[235] = [280, 'Saturday', 'Time4', 'ON', 'Minute']
hmDCBTimers[236] = [281, 'Saturday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[237] = [282, 'Saturday', 'Time4', 'OFF', 'Minute']
hmDCBTimers[238] = [283, 'Sunday', 'Time1', 'ON', 'Hour']
hmDCBTimers[239] = [284, 'Sunday', 'Time1', 'ON', 'Minute']
hmDCBTimers[240] = [285, 'Sunday', 'Time1', 'OFF', 'Hour']
hmDCBTimers[241] = [286, 'Sunday', 'Time1', 'OFF', 'Minute']
hmDCBTimers[242] = [287, 'Sunday', 'Time2', 'ON', 'Hour']
hmDCBTimers[243] = [288, 'Sunday', 'Time2', 'ON', 'Minute']
hmDCBTimers[244] = [289, 'Sunday', 'Time2', 'OFF', 'Hour']
hmDCBTimers[245] = [290, 'Sunday', 'Time2', 'OFF', 'Minute']
hmDCBTimers[246] = [291, 'Sunday', 'Time3', 'ON', 'Hour']
hmDCBTimers[247] = [292, 'Sunday', 'Time3', 'ON', 'Minute']
hmDCBTimers[248] = [293, 'Sunday', 'Time3', 'OFF', 'Hour']
hmDCBTimers[249] = [294, 'Sunday', 'Time3', 'OFF', 'Minute']
hmDCBTimers[250] = [295, 'Sunday', 'Time4', 'ON', 'Hour']
hmDCBTimers[251] = [296, 'Sunday', 'Time4', 'ON', 'Minute']
hmDCBTimers[252] = [297, 'Sunday', 'Time4', 'OFF', 'Hour']
hmDCBTimers[253] = [298, 'Sunday', 'Time4', 'OFF', 'Minute']
