def hmForwardDCBValues(hmStatData, hmOverride):
    # Forward the DCB values to the MQTT Broker
    hmDeviceID = hmStatData[3]

    # Check to make sure the response is from a PRT or PRT-HW device, 2 = PRT 4 = PRT-HW
    if hmStatData[13] in [2, 4]:
        for loop in hmDCBStructure:
            if loop > 87 and hmStatData[13] == 4 and hmStatData[25] == 0:
                continue
            if loop > 55 and hmStatData[13] == 2 and hmStatData[25] == 0:
                continue

            # Work with all Single Byte functions
            if hmDCBStructure[loop][2] == 1:

                # Check to see whether the stat supports the WaterState feature (PRT-HW)
                if hmDCBStructure[loop][0] == 42:
                    if hmStatData[13] != 4:
                        hmUpdateConfig(hmDeviceID, loop, 0, hmOverride, hmDCBStructure[loop][3])
                        hmUpdateConfig(hmDeviceID, loop + 1, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])
                        continue

                if 71 <= hmDCBStructure[loop][0] <= 102 or 187 <= hmDCBStructure[loop][0] <= 298:
                    if hmStatData[13] == 4:
                        if 71 <= hmDCBStructure[loop][0] <= 102:
                            hmUpdateConfig(hmDeviceID, loop, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])

                        if hmStatData[25] == 1 and 187 <= hmDCBStructure[loop][0] <= 298:
                            hmUpdateConfig(hmDeviceID, loop, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])

                    continue

                if 103 <= hmDCBStructure[loop][0] <= 186:
                    if hmStatData[25] == 1:
                        if hmStatData[13] == 2:
                            if loop + 1 < len(hmDCBStructure):
                                hmUpdateConfig(hmDeviceID, loop + 1, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])

                        if hmStatData[13] == 4:
                            hmUpdateConfig(hmDeviceID, loop, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])

                    continue

                if hmDCBStructure[loop][0] > 42:
                    if hmStatData[13] == 2:
                        if loop + 1 < len(hmDCBStructure):
                            hmUpdateConfig(hmDeviceID, loop + 1, hmStatData[hmDCBStructure[loop][0] + hmDCBStructure[loop][4]], hmOverride, hmDCBStructure[loop][3])
                        continue

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


