#!/usr/bin/env python
import os
#from constants import xmlfilename

# Logging Variables
xmltempfilename = 'temp.xml'
xmlfilename = 'heatmiserconfig.xml'

# Main routine to update / create the xml configuration file
# Will support the creation of 6 levels of data within the xml file
def xmlupdate(thermostatID, setting, value, level2, level2name, level3, level3name, level4, level4name, level5, level5name):
    matchlevel = 0
    
    indentlevels = 5
    if level5 == "":
        indentlevels -= 1
        if level4 == "":
            indentlevels -= 1
            if level3 == "":
                indentlevels -= 1
                if level2 == "":
                    indentlevels -= 1
    
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
            
            if indentlevels >> 1:
                if level2 != "":
                    if matchlevel == 1:
                        if line.find("<" + level2 + " name=" + level2name + ">") != -1:
                            matchlevel = 2
                        if line.find("</thermostatID>") != -1:
                            space = ''
                            space += ' ' * ((indentlevels - 4) * 4)
                            filewrite.write(space + "<" + level2 + " name=" + level2name + ">\r\n")
                            filewrite.write(space + "</" + level2 + ">\r\n")
                else:
                    return
                
            if indentlevels >> 2:
                if level3 != "":
                    if matchlevel == 2:
                        if line.find("<" + level3 + " name=" + level3name + ">") != -1:
                            matchlevel = 3
                        if line.find("</" + level2 + ">") != -1:
                            space = ''
                            space += ' ' * ((indentlevels - 3) * 4)
                            filewrite.write(space + "<" + level3 + " name=" + level3name + ">\r\n")
                            filewrite.write(space + "</" + level3 + ">\r\n")
                else:
                    return
                
            if indentlevels >> 3:
                if level4 != "":
                    if matchlevel == 3:
                        if line.find("<" + level4 + " name=" + level4name + ">") != -1:
                            matchlevel = 4
                        if line.find("</" + level3 + ">") != -1:
                            space = ''
                            space += ' ' * ((indentlevels - 2) * 4)
                            filewrite.write(space + "<" + level4 + " name=" + level4name + ">\r\n")
                            filewrite.write(space + "</" + level4 + ">\r\n")
                else:
                    return
                
            if indentlevels >> 4:
                if level5 != "":
                    if matchlevel == 4:
                        if line.find("<" + level5 + " name=" + level5name + ">") != -1:
                            matchlevel = 5
                        if line.find("</" + level4 + ">") != -1:
                            space = ''
                            space += ' ' * ((indentlevels - 1) * 4)
                            filewrite.write(space + "<" + level5 + " name=" + level5name + ">\r\n")
                            filewrite.write(space + "</" + level5 + ">\r\n")
                else:
                    return
                
            if setting == "" or value == "":
                if matchlevel == 5:
                    if line.find("<" + setting + ">" + value + "</" + setting + ">") != -1:
                        matchlevel = 6
                        filewrite.write(line)
                        continue 
                    if line.find("<" + setting + ">") != -1:
                        space = ''
                        space += ' ' * ((indentlevels - 0) * 4)
                        filewrite.write(space + "<" + setting + ">" + value + "</" + setting + ">\r\n")
                        matchlevel = 6
                        continue
                    if line.find("</" + level5 + ">") != -1:
                        space = ''
                        space += ' ' * ((indentlevels - 0) * 4)
                        filewrite.write(space + "<" + setting + ">" + value + "</" + setting + ">\r\n")
                        matchlevel = 6
            else:
                return
            
            filewrite.write(line)
            
        if matchlevel == 0:
            filewrite.write("<thermostatID" + str(thermostatID) + ">\r\n")
            filewrite.write("</thermostatID>\r\n")
        
        # Close files
        filewrite.close()
        fileread.close()
        os.remove(xmlfilename)
        os.rename(xmltempfilename, xmlfilename)
