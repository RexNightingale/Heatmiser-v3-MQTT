#!/usr/bin/env python 

import paho.mqtt.client as mqtt
import socket
import binascii
import sys
import time
import datetime

#Global variable definitions
from constants import *
from mqtt import outboundMQTTqueue

# Things To DO
# Error logging to log file
# Transaction logging to log file

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
        """Calculates a CRC"""
        for c in message:
            self.CRC16_Update(c)
        return [self.low, self.high]


def hmFormMsg(destination, function, start, payload):
    # Creates a message for sending to thermostats, excluding the CRC code
    start_low = (start & BYTEMASK)
    start_high = (start >> 8) & BYTEMASK
    
    # Check to see if this is a Read request
    if function == FUNC_READ:
        payloadLength = 0
        length_low = (RW_LENGTH_ALL & BYTEMASK)
        length_high = (RW_LENGTH_ALL >> 8) & BYTEMASK
        msg = [destination, payloadLength + 10, hmMasterAddress, function, start_low, start_high, length_low, length_high]
    else:
        payloadLength = len(payload)
        length_low = (payloadLength & BYTEMASK)
        length_high = (payloadLength >> 8) & BYTEMASK
        msg = [destination, payloadLength + 10, hmMasterAddress, function, start_low, start_high, length_low, length_high, payload]

    '''
    msg = [destination, payloadLength + 10, hmMasterAddress, function, start_low, start_high, length_low, length_high]
    
    # Check to see if this is a Write request and then add the payload
    if function == FUNC_WRITE:
        msg = msg + payload
    '''
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
        print('Error connecting with the serial interface: %s\n ' % msg)
        s.close()
        connectSerial()
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
    if len(hmStatData) >= 3:        # Just make sure there is something to work with
        
        # Check to ensure the Destination addres = Master Address
        if hmStatData[0] == hmMasterAddress:
            
            # Calculate frame length and make sure this matches with bytes in the frame
            hmFrameLength = hmStatData[2]*256 + hmStatData[1]
            if len(hmStatData) == hmFrameLength:
                
                # Check to see if Slave Address is in the valid range of 1 - 16
                if 1 <= hmStatData[3] <= 16:
                    hmStatCheck = 1     # Looks like an OK message

                # ToDo check to see if the DCB length & Frame length are the same (bytes 7&8 and 10&11)
                # ToDo sort out CRC Checksum
    return hmStatCheck 


def hmSendMQTTMessage(hmMQTTDeviceID, hmMQTTDCBCode, hmMQTTDCBFunction, hmMQTTValue):
    # Send MQTT message to the broker
    # Path is defined as hmMQTTMessagePath + DeviceID + DCB Function + Value
    MQTTMessage = hmMQTTpath + '/' + str(hmMQTTDeviceID) + '/' + str(hmMQTTDCBFunction)

    if hmThermostats[hmMQTTDeviceID, hmMQTTDCBCode] != hmMQTTValue:
        hmThermostats[hmMQTTDeviceID, hmMQTTDCBCode] = hmMQTTValue
        try:
            mqttclient.publish(MQTTMessage, hmMQTTValue)
        except:
            print('error connecting to MQTT Broker')
            

def MQTT_Connect(mqttclient, userdata, rc):
    print("Connected with result code "+str(rc))


def hmRecvMQTTmessage():
    # Check the MQTT Receive queue to see if there are any messages to process
    # Receive queue is filled by mqtt.py
    # Receive Frame format [129, 7, 0, 4, 1, 69, 20]
    if outboundMQTTqueue.qsize() != 0:
        recvMSG = outboundMQTTqueue.get()

        # Loop through all the DCB settings
        for loop in hmDCBStructure:
            if hmDCBStructure[loop][5] == 'RW':

                # Is the message received from the broker equal to the message function in the defined array
                if recvMSG.startswith(hmDCBStructure[loop][1]):
                    destination = int(recvMSG[len(hmDCBStructure[loop][1])+1:recvMSG.find('/', len(hmDCBStructure[loop][1])+1)])
                    
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

                            sendMSG = bytearray(hmFormMsgCRC(destination, FUNC_WRITE, dcbcommand, payload))

                            datal = sendtoSerial(sendMSG)
                    
                            # Check to see if a proper response is received
                            if hmValidateResponse(datal) == 1:
                                if datal[3] == destination:
                                    if datal[4] == FUNC_WRITE:
                                        # ToDo - need to call the refresh of the DCB data to send to the MQTT broker
                                        print('done')
                                    else:
                                        print('failed')
                                else:
                                    print('Incorrect ThermostatID')


def hmForwardDCBValues(hmStatData):
    # Forward the DCB values to the MQTT Broker
    # ToDo look at potential of creating an array for the individual stats and comparing the new values against the array to only send delta information
    # ToDo make more generic and include other functions not used by me
    hmMQTTDeviceID = hmStatData[3]

    # Check to make sure the response is from a PRT or PRT-HW device, 2 = PRT 4 = PRT-HW
    if hmStatData[13] in [2, 4]:
        for loop in hmDCBStructure:

            # Loop through all DCB messages to be included in the outbound MQTT message
            if hmDCBStructure[loop][3] == 1:

                # Work with all Single Byte functions
                if hmDCBStructure[loop][2] == 1:

                    # Check specifically for PRT-HW devices
                    if hmDCBStructure[loop][0] != 42:
                        hmSendMQTTMessage(hmMQTTDeviceID, hmDCBStructure[loop][0], hmDCBStructure[loop][1], hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]])
                    else:
                        if hmStatData[13] == 4:
                            hmSendMQTTMessage(hmMQTTDeviceID, hmDCBStructure[loop][0], hmDCBStructure[loop][1], hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]])

                # Work with all > 1 Byte functions
                else:

                    # Check for Holiday Time
                    if hmDCBStructure[loop][0] == 24:
                        hmMQTTValue = (hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1]
                        hmSendMQTTMessage(hmMQTTDeviceID, hmDCBStructure[loop][0], hmDCBStructure[loop][1], hmMQTTValue)

                    # Check for Room Temperature
                    if hmDCBStructure[loop][0] == 38:
                        hmMQTTValue = float((hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]] * 256) + hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4] + 1])/10
                        hmSendMQTTMessage(hmMQTTDeviceID, hmDCBStructure[loop][0], hmDCBStructure[loop][1], hmMQTTValue)


def bob(hmStatData):
        print('Master Address          : ' + str(hmStatData[0]))
        print('Slave Address           : ' + str(hmStatData[3]))
        print('Model Number            : ' + str(hmStatData[13]))        # 0 = DT, 1 = DT-E, 2 = PRT, 3 = PRT-E, 4 = PRTHW
        print('Temperature Format      : ' + str(hmStatData[14]))        # 0 = C, 1 = F
        print('Slave Address           : ' + str(hmStatData[20]))
        print('Program Mode            : ' + str(hmStatData[25]))        # 0 = 5/2 day mode, 1 = 7 day mode
        if hmStatData[13] == 4:
            print('Day of Week             : ' + str(hmStatData[46]))
            print('Time                    : ' + str(hmStatData[47]) + ' : ' + str(hmStatData[48]) + ' : ' + str(hmStatData[49]))
        else:
            print('Day of Week             : ' + str(hmStatData[45]))
            print('Time                    : ' + str(hmStatData[46]) + ' : ' + str(hmStatData[47]) + ' : ' + str(hmStatData[48]))


def hmTimeUpdate():
    # Update thermostat times
    dayofweek = datetime.datetime.now().isoweekday()
    hour = datetime.datetime.now().time().hour
    mins = datetime.datetime.now().time().minute
    secs = datetime.datetime.now().time().second
    payload = [dayofweek, hour, mins, secs]
    # ToDo - this section is the same in all send / receive functions.  need to create a function
    receiveTimeout = 0.5
    for sendIndex in hmStatList:   
        sendMSG = bytearray(hmFormMsgCRC(sendIndex, FUNC_WRITE, 43, payload))
        
        datal = sendtoSerial(sendMSG)
        
        if hmValidateResponse(datal) == 1:
            if datal[3] == sendIndex:
                if datal[4] == FUNC_WRITE:
                    # Need to call the refresh of the DCB data to send to the MQTT broker
                    print('done')
                else:
                    print('failed')
            else:
                print('Incorrect ThermostatID')


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
            break
        except socket.error, msg:
            print('Error connecting with the serial interface: %s\n ' % msg)
            time.sleep(60)
        

def connectMQTT():
    # Connect to the MQTT Broker
    global mqttclient
    while True:
        mqttclient = mqtt.Client()
        try:
            mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort, 60)
            break
        except:
            print('Error connecting with the MQTT Broker'+ str(rc))
            time.sleep(60)


def main():
    # Sets up the inital array for the Thermostat Data
    hourprocess = 0
    for x in range(0, hmMAXStats + 1):
        for y in range(0, 297):
            hmThermostats[x, y] = 999

    connectSerial()
    connectMQTT()

    while True:
        for sendIndex in hmStatList:
            begin_master = time.time()
            sendMSG = bytearray(hmFormMsgCRC(sendIndex, FUNC_READ, 00, 0))
            
            datal = sendtoSerial(sendMSG)
                       
            # Validate the response from the Thermostats to ensure that an appropriate message has been received for processing
            if hmValidateResponse(datal) == 1:
                # Check to work out what has been sent and forward to the MQTT broker
                hmForwardDCBValues(datal)

            # Process the inbound message stuff
            # Actions happen inbetween the regular polling cycle
            while time.time() - begin_master < 2:
                
                # Process daily job to synchronise the time across all Thermostats
                # Runs at 02:01 to ensure daylight savings time is taken into account
                if datetime.datetime.now().time().hour == 2:
                    if datetime.datetime.now().time().minute == 1:
                        hmTimeUpdate()
                        continue
                
                # ToDo - Process an hourly update of the DCB values for all thermostats and all values and post to MQTT broker
                # ToDo - Uses the MQTT queue for outbound messages
                if datetime.datetime.now().time().minute == 0 and hourprocess == 0:
                    hourprocess = 1
                if datetime.datetime.now().time().minute == 1:
                    hourprocess = 0
                    
                # Look to see if there are any messages from the MQTT Broker to process
                # Process 1 message at a time.
                hmRecvMQTTmessage()
                
                # Wait to 1/100th of a second
                time.sleep(0.01)

    s.close()
            
if __name__ == '__main__': main()