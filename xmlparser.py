#!/usr/bin/env python
import os
from constants import xmlfilename

# Logging Variables
xmltempfilename = 'temp.xml'

def writexml(thermostatID, level2, level2name, level3, level3name, level4, level4name, level5, level5name, setting, value):
    matchlevel = 0
    
    # Open files for processing
    filewrite = open(xmltempfilename, "w")
    fileread = open(xmlfilename, "r")
    
    # Write the xml headers
    filewrite.write('<?xml version="1.0" encoding="UTF-8" ?>\r\n')
    
    for line in fileread:
        # Skip the XML headers section
        if line.find("<?xml") != -1:
            continue

        # Locate the right thermostatID
        if line.find("<thermostatID name=" + str(thermostatID) + ">") != -1:
            matchlevel = 1
            
        # Locate the right configuration section
        if matchlevel == 1:
            if line.find("<" + field1 + " name=" + field2 + ">") != -1:
                matchlevel = 2
            if line.find("</thermostatID>") != -1:
                filewrite.write("    <" + field1 + " name=" + field2 + ">\r\n)
                filewrite.write("        <" + field3 + " name=" + field4 + ">\r\n")
                filewrite.write("            <" + field5 + " name=" + field6 + ">\r\n")
                filewrite.write("                <" + field7 + ">" + value + "</" + field7 + ">\r\n")
                filewrite.write("            </" + field5 + ">\r\n")
                filewrite.write("        </" + field3 + ">\r\n")
                filewrite.write("    </" + field1 + ">\r\n")
                matchlevel = 0
                
        # Locate the right day zone
        if matchlevel == 2:
            if line.find("<" + field3 + " name=" + field4 + ">") != -1:
                matchlevel = 3
            if line.find("</" + field1 + ">") != -1:
                filewrite.write("        <" + field3 + " name=" + field4 + ">\r\n")
                filewrite.write("            <" + field5 + " name=" + field6 + ">\r\n")
                filewrite.write("                <" + field7 + ">" + value + "</" + field7 + ">\r\n")
                filewrite.write("            </" + field5 + ">\r\n")
                filewrite.write("        </" + field3 + ">\r\n")
                matchlevel = 1
                
        # Locate the right time zone
        if matchlevel == 3:
            if line.find("<" + field5 + " name=" + field6 + ">") != -1:
                matchlevel = 4
            if line.find("</" + field3 + ">") != -1:
                filewrite.write("            <" + field5 + " name=" + field6 + ">\r\n")
                filewrite.write("                <" + field7 + ">" + value + "</" + field7 + ">\r\n")
                filewrite.write("            </" + field5 + ">\r\n")
                matchlevel = 2
        
        # Locate the right configuration setting
        if matchlevel == 4:
            if line.find("<" + field7 + ">") != -1:
                filewrite.write("                <" + field7 + ">" + value + "</" + field7 + ">\r\n")
                matchlevel = 5
                continue
            if line.find("</" + field5 + ">") != -1:
                filewrite.write("                <" + field7 + ">" + value + "</" + field7 + ">\r\n")
                matchlevel = 5
                                
        filewrite.write(line)
        
    # Close files
    filewrite.close()
    fileread.close()
    os.remove(xmlfilename)
    os.rename(xmltempfilename, xmlfilename)
    
def main():
    # writexml(thermostatID, field1, field2, field3, field4, field5, field6, field7, value)
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "hour", "09")
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "minute", "00")
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "temp", "20")


if __name__=="__main__": main()
