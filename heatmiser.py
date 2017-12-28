#!/usr/bin/env python 

import paho.mqtt.client as mqtt
import socket
import binascii
import sys
import time
import datetime

#Global variable definitions
from constants import *
from logger import logmessage
from mqtt import outboundMQTTqueue
from xmlparser import xmlupdate

# Creation of the Twitter interface  
api = tweepy.API(twAuth)

class crc16:
    LookupHigh = [
    0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
    0x81, 0x91, 0xa1, 0xb1, 0xc1, 0xd1, 0xe1, 0xf1
    ]
    LookupLow = [
    0x00, 0x21, 0x42, 0x63, 0x84, 0xa5, 0xc6, 0xe7,
    0x08, 0x29, 0x4a, 0x6b, 0x8c, 0xad, 0xce, 0xef
    ]
    def __init__(self):
        self.high = BYTEMASK
        self.low = BYTEMASK

    def Update4Bits(self, val):
        # Step one, extract the Most significant 4 bits of the CRC register
        t = self.high>>4

        # XOR in the Message Data into the extracted bits
        t = t^val

        # Shift the CRC Register left 4 bits
        self.high = (self.high << 4)|(self.low>>4)
        self.high = self.high & BYTEMASK    # force char
        self.low = self.low <<4
        self.low = self.low & BYTEMASK  # force char

        # Do the table lookups and XOR the result into the CRC tables
        self.high = self.high ^ self.LookupHigh[t]
        self.high = self.high & BYTEMASK    # force char
        self.low  = self.low  ^ self.LookupLow[t]
        self.low = self.low & BYTEMASK  # force char

    def CRC16_Update(self, val):
        self.Update4Bits(val>>4) # High nibble first
        self.Update4Bits(val & 0x0f) # Low nibble

    def run(self, message):
        # Calculates the CRC
        for c in message:
            self.CRC16_Update(c)
        return [self.low, self.high]


def hmFormMsg(destination, function, start, payload):
    # Creates a message for sending to thermostats, excluding the CRC code
    start_low = (start & BYTEMASK)
    start_high = (start >> 8) & BYTEMASK
    if function == FUNC_READ:
        payloadLength = 0
        length_low = (RW_LENGTH_ALL & BYTEMASK)
        length_high = (RW_LENGTH_ALL >> 8) & BYTEMASK
    else:
        payloadLength = len(payload)
        length_low = (payloadLength & BYTEMASK)
        length_high = (payloadLength >> 8) & BYTEMASK
    msg = [destination, 10+payloadLength, hmMasterAddress, function, start_low, start_high, length_low, length_high]
    if function == FUNC_WRITE:
        msg = msg + payload
    return msg


def hmFormMsgCRC(destination, function, start, payload):
    # Creates a message for sending to thermostats, including the CRC code
    data = hmFormMsg(destination, function, start, payload)
    crc = crc16()
    data = data + crc.run(data)
    return data


def sendtoSerial(sendMSG):
    # Send data to the serial interface for the thermostats
    receiveTimeout = 0.5
    datal = []
    recvMSG = ''
    try:
        s.send(sendMSG)
    except socket.error, msg:
        logmessage('error', 'heatmiser.py', 'Error connecting with the serial interface: ' + str(msg))
        s.close()
        connectSerial()
        time.sleep(10)
        return datal

    begin = time.time()

    while 1:
        if datal and time.time()-begin > receiveTimeout:
            break

        elif time.time()-begin > receiveTimeout*2:
            break

        try:
            recvMSG = s.recv(7)
            if recvMSG:
                datal = datal + (map(ord, recvMSG))
                begin = time.time()
            else:
                time.sleep(0.01)
        except:
            pass
    
    return datal

    
def hmValidateResponse(hmStatData):
    # Validate the response provided from the thermostat
    # Uses Destination Address & Framelength
    # To validate the response
    hmStatCheck = 0

    # Just make sure there is something to work with
    if len(hmStatData) >= 3:
        
        # Check to ensure the Destination addres = Master Address
        if hmStatData[0] == hmMasterAddress:
            
            # Calculate frame length and make sure this matches with bytes in the frame
            hmFrameLength = hmStatData[2]*256 + hmStatData[1]
            if len(hmStatData) == hmFrameLength:
                
                # Check to see if Slave Address is in the valid range of 1 - 32
                if 1 <= hmStatData[3] <= hmMAXStats:
                    hmStatCheck = 1     # Looks like an OK message
                    # ToDo sort out CRC Checksum
    return hmStatCheck 


def SendMQTTMessage(hmDeviceID, hmDCBCode, hmDCBFunction, hmMQTTValue):
    # Send MQTT message to the broker
    # Path is defined as hmMQTTMessagePath + DeviceID + DCB Function + Value
    MQTTMessage = hmMQTTpath + '/' + str(hmDeviceID) + '/' + str(hmDCBFunction)
    logmessage('info', 'heatmiser.py', 'Message sent to MQTT Broker ' + str(MQTTMessage) + ":" + str(hmMQTTValue))
    mqttclient.publish(MQTTMessage, hmMQTTValue)


def hmUpdateConfig(hmDeviceID, DCBStructureCode, value, override, IncludeMQTT):
    # Update the in-memory configuration
    if hmThermostats[hmDeviceID, hmDCBStructure[DCBStructureCode][0]] != value or override == 1:
        if hmThermostats[hmDeviceID, hmDCBStructure[DCBStructureCode][0]] != value:
            hmThermostats[hmDeviceID, hmDCBStructure[DCBStructureCode][0]] = value
        
        # Send MQQT Values
        if IncludeMQTT == 1:
            SendMQTTMessage(hmDeviceID, hmDCBStructure[DCBStructureCode][0], hmDCBStructure[DCBStructureCode][1], value)
    
    
def hmUpdateXML(hmDeviceID, hmDCBCode, value):
    # Update the Heatmiser XML Configuration file
    if hmThermostats[hmDeviceID, hmDCBCode] != value:
        hmThermostats[hmDeviceID, hmDCBCode] = value
        # Model type 2 = PRT
        if hmThermostats[hmDeviceID, 1] == 2:
            if 47 <= hmDCBCode <= 70 or 103 <= hmDCBCode <= 186:
                # Update the XML file with heating settings
                for loop in range(0, 254):
                    if hmDCBTimers[loop][0] == hmDCBCode:
                        xmlupdate(hmDeviceID, hmDCBTimers[loop][4], value, "level", "heatingtimes", "day", hmDCBTimers[loop][1], "timezone", hmDCBTimers[loop][2], "", "")
        # Model type 4 = PRT-H
        if hmThermostats[hmDeviceID, 1] == 4:
            if 71 <= hmDCBCode <= 102 or 187 <= hmDCBCode <= 298:
                # Update the XML file with hotwater settings
                for loop in range(0, 254):
                    if hmDCBTimers[loop][0] == hmDCBCode:
                        xmlupdate(hmDeviceID, hmDCBTimers[loop][4], value, "level", "hotwatertimes", "day", hmDCBTimers[loop][1], "timezone", hmDCBTimers[loop][2], "", "")

    
def on_connect(client, userdata, rc):
    logmessage('info', 'heatmiser.py', 'Connected to MQTT broker')
    #msgTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #api.update_status(status = msgTime + " Connected to the MQTT broker")

    
def on_disconnect(client, userdata, rc):
    logmessage('info', 'heatmiser.py', 'Disconnected from MQTT broker')
    #msgTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #api.update_status(status = msgTime + " Error connecting to the MQTT broker")

    
def hmRecvMQTTmessage():
    # Check the MQTT Receive queue to see if there are any messages to process
    # Receive queue is filled by mqtt.py
    # Receive Frame format [129, 7, 0, 4, 1, 69, 20]
    if outboundMQTTqueue.qsize() != 0:
        recvMSG = outboundMQTTqueue.get()

        # Loop through all the DCB settings
        for loop in hmDCBStructure:
            if hmDCBStructure[loop][5] == 'RW':

                # Is the message received from the broker equal to the message functions in the defined array
                if recvMSG.startswith(hmDCBStructure[loop][1]):
                    destination = int(recvMSG[len(hmDCBStructure[loop][1])+1:recvMSG.find('/', len(hmDCBStructure[loop][1]) + 1)])

                    # Check to make sure the Thermostat ID is in the expect range in hmStatList
                    if destination in hmStatList:
                        dcbcommand = int(hmDCBStructure[loop][0])
                        
                        # Check to make sure the value being sent is within allowable range
                        dcbvalue = int(str(recvMSG[recvMSG.find('/', len(hmDCBStructure[loop][1])+1)+1:len(recvMSG)]).split('.')[0])
                        if hmDCBStructure[loop][6] <= dcbvalue <= hmDCBStructure[loop][7]:
                            
                            # Work out the holiday time
                            if hmDCBStructure[loop][1] == 'HolidayTime':
                                hours = dcbvalue * 24
                                hours_lo = (hours & BYTEMASK)
                                hours_hi = (hours >> 8) & BYTEMASK
                                payload = [hours_lo, hours_hi]
                            else:
                                payload = [dcbvalue]

                            # Send updates to the Thermostat
                            sendMSG = bytearray(hmFormMsgCRC(destination, FUNC_WRITE, dcbcommand, payload))
                            datal = sendtoSerial(sendMSG)
                    
                            # Validate the response from the thermostat
                            if hmValidateResponse(datal) == 1:
                                
                                # Does the receiving data source address match the destination send address
                                if datal[3] == destination:
                                    
                                    # Does the response have a WRITE response in the frame
                                    if datal[4] == FUNC_WRITE:
                                        # Call the refresh of the DCB data for that thermostat
                                        sendMSG = bytearray(hmFormMsgCRC(destination, FUNC_READ, 00, 0))
                                        datal = sendtoSerial(sendMSG)

                                        # Validate the response from the Thermostats to ensure that an appropriate message has been received for processing
                                        if hmValidateResponse(datal) == 1:
                                            # Check to work out what has been sent and forward to the MQTT broker
                                            hmForwardDCBValues(datal, 0)

                                        logmessage('info', 'heatmiser.py', 'Command sent to Thermostat ' + str(destination) + ': ' + str(hmDCBStructure[loop][1]) + ":" + str(dcbvalue))
                                    else:
                                        logmessage('error', 'heatmiser.py', 'Failed to send command to Thermostat: ' + str(destination))
                                else:
                                    logmessage('error', 'heatmiser.py', 'Incorrect ThermostatID response received')


def hmForwardDCBValues(hmStatData, hmOverride):
    # Forward the DCB values to the MQTT Broker
    hmDeviceID = hmStatData[3]

    # Check to make sure the response is from a PRT or PRT-HW device, 2 = PRT 4 = PRT-HW
    if hmStatData[13] in [2, 4]:
        for loop in hmDCBStructure:
            # Work with all Single Byte functions
            if hmDCBStructure[loop][2] == 1:
                    
                # Check to see whether the stat supports the WaterState feature (PRT-HW)
                if hmDCBStructure[loop][0] != 42:
                    hmUpdateConfig(hmDeviceID, loop, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])
                else:
                    if hmStatData[13] == 4:
                        hmUpdateConfig(hmDeviceID, loop, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])

            # Work with all > 1 Byte functions
            else:

                # Calculate the Calibration Offset
                if hmDCBStructure[loop][0] == 8:
                    value = float((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])
                    hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])

                # Calculate Holiday Time
                if hmDCBStructure[loop][0] == 24:
                    value = int((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])/24
                    hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])

                # Calculate Hold Time
                if hmDCBStructure[loop][0] == 32:
                    value = int((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])
                    hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])

                # Calculate Remote Air Temperature
                # 0xffff = no sensor connected
                if hmDCBStructure[loop][0] == 34:
                    value = float((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])/10
                    if value != 6553.5:
                        hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])
                        
                # Calculate Floor Temperature
                # 0xffff = no sensor connected
                if hmDCBStructure[loop][0] == 36:
                    value = float((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])/10
                    if value != 6553.5:
                        hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])

                # Calculate Built-in Air Temperature
                if hmDCBStructure[loop][0] == 38:
                    value = float((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])/10
                    hmUpdateConfig(hmDeviceID, loop, value, hmOverride, hmDCBStructure[loop][3])


def hmGetTimerValues(hmStatData):
    # Get the Timer values for the thermostats
    hmDeviceID = hmStatData[3]

    # Clear all timer values for the thermostat
    #del hmThermostatTimers[hmDeviceID][:] 

    # Append thermostat ID value, Thermostat Type, Program Mode
    #hmThermostatTimers[hmDeviceID].append(hmDeviceID)
    #hmThermostatTimers[hmDeviceID].append(hmStatData[13])
    #hmThermostatTimers[hmDeviceID].append(hmStatData[25])
    #hmThermostatTimers[hmDeviceID].append(hmStatData[loop + offset])
    
    # Check to make sure the response is from a PRT or PRT-HW device, 2 = PRT 4 = PRT-HW
    if hmStatData[13] in [2, 4]:
    
        # Get Heating timer values
        # Check to see if program mode is 5/2 Days
        if hmStatData[25] == 0:
            settingsrange = 24
            # If thermostat type is type 2 PRT
            if hmStatData[13] == 2:
                offset = 49
            # If thermostat type is type 4 PRTH
            elif hmStatData[13] == 4:
                offset = 50
                # Append hotwater timer values
                for loop in range(0, 32):
                    hmUpdateXML(hmDeviceID, loop + 74, hmStatData[loop + 74]):
                    #hmThermostats[hmDeviceID, loop + 74] = hmStatData[loop + 74]

        # Get 7 day program mode values
        else:
            settingsrange = 84
            # If thermostat type is type 2 PRT
            if hmStatData[13] == 2:
                offset = 73
            # If thermostat type is type 4 PRTH
            elif hmStatData[13] == 4:
                offset = 106
                # Append hotwater timer values
                for loop in range(0, 112):
                    hmUpdateXML(hmDeviceID, loop + 190, hmStatData[loop + 190]):
                    #hmThermostats[hmDeviceID, loop + 190] = hmStatData[loop + 190]

        # Append heating timer values
        for loop in range(0, settingsrange):
            hmUpdateXML(hmDeviceID, loop + offset, hmStatData[loop + offset]):
            #hmThermostats[hmDeviceID, loop + offset] = hmStatData[loop + offset]

                
def hmTimeUpdate():
    # Update thermostat times
    dayofweek = datetime.datetime.now().isoweekday()
    hour = datetime.datetime.now().time().hour
    mins = datetime.datetime.now().time().minute
    secs = datetime.datetime.now().time().second
    payload = [dayofweek, hour, mins, secs]

    for sendIndex in hmStatList:   
        sendMSG = bytearray(hmFormMsgCRC(sendIndex, FUNC_WRITE, 43, payload))

        datal = sendtoSerial(sendMSG)

        if hmValidateResponse(datal) == 1:
            if datal[3] == sendIndex:
                if datal[4] == FUNC_WRITE:
                    logmessage('info', 'heatmiser.py', 'Time updated for Thermostat ID: ' + str(sendIndex))
                else:
                    logmessage('error', 'heatmiser.py', 'Failed to update time for Thermostat ID: ' + str(sendIndex))
            else:
                logmessage('error', 'heatmiser.py', 'Incorrect ThermostatID response received')


def connectSerial():
    # Start a few things off before we get going
    # Connect to the Serial interface for the Heatmiser Thermostats
    global s
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((hmSerialIP, hmSerialPort))
            s.settimeout(hmSerialTimeout)
            s.setblocking(0)
            time.sleep(0.5)
            logmessage('info', 'heatmiser.py', 'Connected to the serial interface')
            break
        except socket.error, msg:
            logmessage('error', 'heatmiser.py', 'Error connecting with the serial interface: ' + str(msg))
            #msgTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            #api.update_status(status = msgTime + " Error connecting with the serial interface")
            time.sleep(60)
        

def connectMQTT():
    # Connect to the MQTT Broker
    global mqttclient
    while True:
        mqttclient = mqtt.Client()
        mqttclient.on_connect = on_connect
        mqttclient.on_disconnect = on_disconnect
        try:
            mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort)
            mqttclient.loop_start()
            break
        except:
            logmessage('error', 'heatmiser.py', 'Error connecting to the MQTT Broker')
            time.sleep(30)


def main():
    # Sets up the inital array for the Thermostat Data
    for x in range(1, hmMAXStats + 1):
        for y in range(1, 299):
            hmThermostats[x, y] = 999

    # Set the initial values for process variables
    hourprocess = 0
    timeprocess = 0
    
    # Connect to the Serial interface and MQTT Broker
    connectSerial()
    connectMQTT()

    while True:
        # Process an hourly update of the DCB values for all thermostats and all values and post to MQTT broker
        if datetime.datetime.now().time().minute == 0:
            if hourprocess == 0:
                hourprocess = 1
            elif hourprocess == 1:
                hourprocess = 2
        if datetime.datetime.now().time().minute == 1:
            hourprocess = 0

        for sendIndex in hmStatList:
            begin_master = time.time()

            # Poll the thermostats for updates
            sendMSG = bytearray(hmFormMsgCRC(sendIndex, FUNC_READ, 00, 0))
            datal = sendtoSerial(sendMSG)
            
            # Validate the response from the Thermostats to ensure that an appropriate message has been received for processing
            if hmValidateResponse(datal) == 1:
                # Check to work out what has been sent and forward to the MQTT broker
                hmForwardDCBValues(datal, hourprocess)
                hmGetTimerValues(datal)

            # Process the inbound message stuff
            # Actions happen inbetween the regular polling cycle
            while time.time() - begin_master < hmPollCycle:
                
                # Process daily job to synchronise the time across all Thermostats
                # Runs at 03:00 to ensure daylight savings time is taken into account
                if datetime.datetime.now().time().hour == 3:
                    if datetime.datetime.now().time().minute == 0 and timeprocess == 0:
                        hmTimeUpdate()
                        timeprocess = 1
                    elif datetime.datetime.now().time().minute == 1:
                        timeprocess = 0

                # Look to see if there are any messages from the MQTT Broker to process
                # Process 1 message at a time.
                hmRecvMQTTmessage()
                
                # Wait to 1/100th of a second
                time.sleep(0.01)

    s.close()
            
if __name__ == '__main__': main()
