# Heatmiser-v3-MQTT
Python Code to interact with the Heatmiser v3 Thermostats and interface with an MQTT Broker

After finding limitations on various implementations of code to interact with the Heatmiser v3 Thermostats, I decided to coble together my own variation and building on the work done by various folk and borrowing various pieces of code (and therefore recognition to the following is needed for the inspiration):
- Neil Trimboy
- Andy Lockran

I have finally come up with a small Python bit of code to interact with the Heatmiser v3 Thermostats using an IP to RS485 converter and to use an MQTT Broker to act as the external interface to any home automation applications.

I will confess that I am only a hobbyist and therefore the code may not be optimal but it works for what I require.

I will provide more details on the total project shortly.

# Connecting the Heatmiser system to the network

For this I have used the GC-ATC-1000 TCP/IP to RS232/422/485 Converter.  There are others on the market however, preference is yours.

# Monitoring Hardware

For the actual running of the scripts I have just used a standard Raspberry PI Model B.  It does not have to be that powerful for this lot.  As it happens I have been using 1 for monitoring my boiler, so it was just easy to use.

In theory when running the scripts and assuming that you have set the right IP addresses and port numbers, then this should just all fire up and off you go.  However, I did have quite a few teething problems when starting off.  Trial and error with a lot of this and a good dose of WireShark.
