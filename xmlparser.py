#!/usr/bin/env python

# Logging Variables
xmlfilename = 'heatmiserconfig.xml'
xmltempfilename = 'temp.xml'


def writexml(thermostatID, level, field1, field2, field3, field4, field5, value):
    matchlevel =0
    
    # Open files for processing
    filewrite = open(xmltempfilename, "w")
    fileread = open(xmlfilename, "a")
    
    # Write the xml headers
    filewrite.write('<?xml version="1.0" encoding="UTF-8" ?>\r\n')
    #filewrite.write("\r\n")
    
    for line in fileread:
        # Skip the XML headers section
        if line.find("<?xml") != -1:
            continue
        
        if matchlevel >= 1:
            if line.find("<" + level + ">") != -1:
                matchlevel = 2
            if matchlevel >=2:
                if line.find("<" + field1 + " name=" + field2 + ">") != -1:
                    matchlevel = 3
                if matchlevel >= 3:
                    if line.find("<" + field3 + " name=" + field4 + ">") != -1:
                        matchlevel = 4
                    if matchlevel >= 4:
                        if line.find("<" + field5 + ">" + str(value) + "</" + field5 + ">") != -1:
                            matchlevel = 5

            filewrite.write(line)                
                
        if matchlevel == 0:
            # Locate the right thermostatID
            if line.find("<thermostatID name=" + str(thermostatID) + ">") != -1:
                filewrite.write("<thermostatID name=" + str(thermostatID) + ">\r\n")
                matchlevel = 1
            else:
                filewrite.write(line)
        
#    filewrite.write("<thermostatID name=" + str(thermostatID) + ">\r\n")
#    if level in ('config' , 'heatingtimes' , 'hotwatertimes'):
#        filewrite.write("    <" + level + ">\r\n")
#        filewrite.write("        <" + field1 + " name=" + field2 + ">\r\n")
#        filewrite.write("            <" + field3 + " name=" + field4 + ">\r\n")
#        filewrite.write("                <" + field5 + ">" + str(value) + "</" + field5 + ">\r\n")
#        filewrite.write("            </" + field3 + ">\r\n")
#        filewrite.write("        </" + field1 + ">\r\n")
#        filewrite.write("    </" + level + ">\r\n")
#    filewrite.write("</thermostatID>\r\n")
    
    # Close files
    filewrite.close()
    fileread.close()
    
def main():
    # writexml(thermostatID, level, field1, field2, field3, field4, field5, value)
    writexml(1, "heatingtimes", "day", "weekday", "timezone", "time1", "hour", "09")


if __name__=="__main__": main()
