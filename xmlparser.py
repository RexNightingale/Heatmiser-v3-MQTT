#!/usr/bin/env python
import os
from constants import xmlfilename

# Logging Variables
xmltempfilename = 'temp.xml'

def writexml(thermostatID, level2, level2name, level3, level3name, level4, level4name, level5, level5name, setting, value):
    matchlevel = 0
    
    while matchlevel != 6:
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
            if matchlevel == 1:
                if line.find("<" + level2 + " name=" + level2name + ">") != -1:
                    matchlevel = 2
                if line.find("</thermostatID>") != -1:
                    space = ''
                    space += ' ' * 1
                    filewrite.write(space + "<" + level2 + " name=" + level2name + ">\r\n")
                    filewrite.write(space + "</" + level2 + ">\r\n")

            if matchlevel == 2:
                if line.find("<" + level3 + " name=" + level3name + ">") != -1:
                    matchlevel = 3
                if line.find("</" + level2 + ">") != -1:
                    space = ''
                    space += ' ' * 2
                    filewrite.write(space + "<" + level3 + " name=" + level3name + ">\r\n")
                    filewrite.write(space + "</" + level3 + ">\r\n")
            
            if matchlevel == 3:
                if line.find("<" + level4 + " name=" + level4name + ">") != -1:
                    matchlevel = 4
                if line.find("</" + level3 + ">") != -1:
                    space = ''
                    space += ' ' * 3
                    filewrite.write(space + "<" + level4 + " name=" + level4name + ">\r\n")
                    filewrite.write(space + "</" + level4 + ">\r\n")
            
            if matchlevel == 4:
                if line.find("<" + level5 + " name=" + level5name + ">") != -1:
                    matchlevel = 5
                if line.find("</" + level4 + ">") != -1:
                    space = ''
                    space += ' ' * 4
                    filewrite.write(space + "<" + level5 + " name=" + level5name + ">\r\n")
                    filewrite.write(space + "</" + level5 + ">\r\n")
            
            if matchlevel == 5:
                # write the level6 values
                something(setting, value, 6)
                matchlevel = 6

            if matchlevel != 6:
                filewrite.write(line)

        # Close files
        filewrite.close()
        fileread.close()
        os.remove(xmlfilename)
        os.rename(xmltempfilename, xmlfilename)

            
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
                                
def something(node, value, offset):
    space += ' ' * offset
    filewrite.write(space + "<" + node + ">" + value + "</" + node + ">\r\n")


def somethingelse(node, value, offset):
    space += ' ' * offset
    filewrite.write(space + "<" + node + " name=" + value + ">\r\n")
    filewrite.write(space + "</" + node + ">\r\n")
               
                                
def main():
    # writexml(thermostatID, field1, field2, field3, field4, field5, field6, field7, value)
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "hour", "09")
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "minute", "00")
    writexml(1, "level", "heatingtimes", "day", "weekday", "timezone", "time1", "temp", "20")


if __name__=="__main__": main()
