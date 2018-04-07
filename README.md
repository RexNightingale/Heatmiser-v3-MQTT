# Heatmiser-v3-MQTT
Python Code to interact with the Heatmiser v3 Thermostats and interface with an MQTT Broker

After finding limitations on various implementations of code and home automation systems interacting with the Heatmiser v3 Thermostats, I decided to coble together my own variation and building on the work done by various folk and borrowing various pieces of code (and therefore recognition to the following is needed for the inspiration):
- Neil Trimboy
- Andy Lockran
- Flatsheep

I have finally come up with a small Python bit of code to interact with the Heatmiser v3 Thermostats using an IP to RS485 converter and to use an MQTT Broker to act as the external interface, which in my case I will be connecting up to my Openhab installation, but you could use it for any purpose really..

I will confess that I am only a hobbyist and therefore the code may not be optimal but it works for what I require.

# Heatmiser Serial Interface

To connect the Heatmiser Thermostats to the network, I have used the GC-ATC-1000 TCP/IP to RS232/422/485 Converter.  There are others on the market however, the more you spend the more features you get with them, preference is yours.  Originally I had been using this with my Openhab set up and the Heatmiser Binding quite happily so I knew it worked, but limitations on the Openhab Binding drove me to this route.  

# Raspberry Pi

For the actual running of the scripts I have just used a Raspberry PI Model B.  It does not have to be that powerful for this lot.  As it happens I have been using one for monitoring my boiler, so it was just as easy to use that.

In theory when running the scripts and assuming that you have set the right IP addresses and port numbers, then this should just all fire up and off you go.  However, I did have quite a few teething problems when starting off.  Trial and error with a lot of this and a good dose of WireShark.

# MQTT Broker

For my installation I have used the Moquitto MQTT Broker installed on a second Raspberry Pi which sits on the Openhab server.  Again it should not really matter what broker you want to use.  If you go for a hosted MQTT Broker then you will probably have to modify the MQTT Broker connect functions in 'heatmiser.py' and 'mqtt.py'

# The Code Blocks

There are four main code blocks:

### constants.py

Used to store all the static global variables used by all the various utilities

### mqtt.py

This utility quite simply monitors the MQTT Broker for those topics which are required, as defined within the thermostat array from 'constants.py' and places any updates received into a queue for processing within 'heatmiser.py'.  As the interface with the Thermostats was only ever desiged as a serial process interface with a single master, I needed to use a single script to control the comms with the thermostats

### logger.py

Just really used to log any messages generated from 'heatmiser.py' and 'MQTT.py'.

### heatmiser.py

This is the main engine of the whole thing.  However to simplify this a bit:
- The script polls the thermostats on a regular basis and posts any updates needed to the MQTT Broker
- Only changes are sent to the MQTT Broker not all updates from each poll cycle
- Inbetween each poll the script sees if there is anything to process from the MQTT Broker and processes 1 message every poll cycle, as the message rates aren't high
- Every hour the script updates everything to the MQTT Broker, just in-case
- Every day at 03:00, the script updates the time of every Thermostat

That's it..

# Installation

There's not much too this one from an installation perspective, copy the files into the directory of your choosing, update 'constants.py' with your local settings and set to run 'heatmiser.py' automatically on boot.  However, there are a few pre-requisites that you will need:

### SQL Lite 3
This is proven to work with SQLlite3 v3.23.0.
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install sqlite3
```

Now to setup the SQLite Database for use by this utility.  I usually set this up in the same directory as the main Python code:
```
sqlite3 heatmiser.db
```
Now to setup the table:
```
CREATE TABLE thermostats (ThermostatID INT, DCBCode INT, DCBCodeName TEXT, Value INT);
```
You might want to set up specific permissions within the SQLite Database, but I havent done this here (shame on me).

And finally exit SQLite:
```
.exit
```
### Paho MQTT
This is proven to work with v1.3.1 of the Paho MQTT client:
```
pip install paho-mqtt
```

### Tweepy
This is proven to work with v3.6.0 of the Tweepy client:
```
pip install tweepy
```

### Queue Library
This is proven to work with v1.5.0 of the QueueLib library:
```
pip install queuelib
```
### 'heatmiser.py' run at start-up
To set heatmiser.py to run automatically on start add an entry into the crontab file like so:
```
crontab -e
```
add this line to the end of the crontab file.  Remember to replace '/home/pi/' with the directory of your choosing:
```
@reboot python /home/pi/heatmiser.py /home/pi/crontablog.log 2>&1
```
and then exit the crontab utility and reboot...all being well you should have a fully functioning system

# Future Plans

For the future I plan to create a web interface to this utility such that I can interact a bit more with the Thermostats, especially for functions like controlling centrally the On/Off timers, where a home automation system may not be that ideal for this and gives you the ability to run the heating off-line.

Also I intend to integrate the boiler monitoring scripts such that I can better control and monitor this.  My specific set-up is a Biomass Boiler, so needs a little more TLC than just a bog standard wall-hung gas or oil boiler.
