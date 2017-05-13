#!/usr/bin/env python

import Queue
import paho.mqtt.client as mqtt
import time
from constants import *
from logger import logmessage

outboundMQTTqueue = Queue.Queue()

def on_connect(client, userdata, rc):
	# Do something when connected to MQTT Broker
	logmessage('info', 'mqtt.py', 'Connected to broker')
	
	# Go through all the entries in the hmDCBStructure array
	for loop in hmDCBStructure:
		# Find only those which have a status of 'RW'
		# Then subscribe to each element
		if hmDCBStructure[loop][5] == 'RW':
			hmMQTTSubscribePath = hmMQTTpath + "/" + hmDCBStructure[loop][1] + "/#"
			mqttclient.subscribe(hmMQTTSubscribePath)
			logmessage('info', 'mqtt.py', 'Subscribed to MQTT Broker using path ' + hmMQTTSubscribePath)


def on_disconnect(client, userdata, rc):
	# Do something when connected to MQTT Broker
	logmessage('warning', 'mqtt.py', 'Disconnected from MQTT Broker')


def on_message(client, userdata, msg):
	# Process messages received from MQTT Broker
	# Place the messages received in the 'outboundMQTTqueue queue'
	# Format of message = DCB Function/Thermostat ID/DCB Value
	# Assumes that the DCB Function, Thermostat ID and Value are all correct
	if msg.topic.startswith(hmMQTTpath):
		queuemsg = msg.topic[len(hmMQTTpath)+1:len(msg.topic)] + "/" + str(msg.payload)
		outboundMQTTqueue.put(queuemsg)
		logmessage('info', 'mqtt.py', 'Message received from MQTT Broker ' + queuemsg)


# Start the MQTT Client
mqttclient = mqtt.Client()
mqttclient.on_connect = on_connect
mqttclient.on_message = on_message
mqttclient.on_disconnect = on_disconnect
while True:
	mqttclient = mqtt.Client()
	mqttclient.on_connect = on_connect
	mqttclient.on_message = on_message
	mqttclient.on_disconnect = on_disconnect
	try:
		mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort)
		break
	except:
		logmessage('error', 'mqtt.py', 'Error connecting to MQTT Broker')
		time.sleep(30)
		

# Perform an infinate loop to receive messages from the MQTT Broker
mqttclient.loop_start()



















