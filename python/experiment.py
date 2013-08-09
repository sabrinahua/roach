#!/usr/bin/env python
"""
authors: stanbaek, apullin

"""
from lib import command
import time,sys
import serial
import shared

from hall_helpers import *

def main():    
    setupSerial()

    # Send robot a WHO_AM_I command, verify communications
    queryRobot()
    #Motor gains format:
    #  [ Kp , Ki , Kd , Kaw , Kff     ,  Kp , Ki , Kd , Kaw , Kff ]
    #    ----------LEFT----------        ---------_RIGHT----------
    motorgains = [1800,20,100,0,0, 1800,20,100,0,0]
    duration = 500
    vel = 0
    turn_rate = 0
    telemetry = True
    repeat = False

    params = hallParams(motorgains, duration, vel, turn_rate, telemetry, repeat)
    setMotorGains(motorgains)

    leadIn = 10
    leadOut = 10
    strideFreq = 5
    useFlag = 0
    deltas = [0.25, 0.1, 0.25, 0.25, 0.25, 0.25]

    manParams = manueverParams(leadIn, leadOut, strideFreq, useFlag, deltas)

    while True:

        if not(params.repeat):
            settingsMenu(params, manParams)   

        if params.telemetry:
            # Construct filename
            path     = 'Data/'
            name     = 'trial'
            datetime = time.localtime()
            dt_str   = time.strftime('%Y.%m.%d_%H.%M.%S', datetime)
            root     = path + dt_str + '_' + name
            shared.dataFileName = root + '_imudata.txt'
            print "Data file:  ", shared.dataFileName
            if manParams.useFlag == True:
                duration = 1.0/manParams.strideFreq * (manParams.leadIn + 1 + manParams.leadOut)
                numSamples = int(ceil(1000 * duration))
            else:
                numSamples = int(ceil(1000 * (params.duration + shared.leadinTime + shared.leadoutTime) / 1000.0))
            eraseFlashMem(numSamples)

        # Pause and wait to start run, including leadin time
        raw_input("Press enter to start run ...") 
        # Trigger telemetry save, which starts as soon as it is received
        if params.telemetry:
            startTelemetrySave(numSamples)
        #Start robot
        if manParams.useFlag == True:
            print 'test'
            runManuver(params, manParams)
        else:
            xb_send(0, command.START_TIMED_RUN, pack('h',params.duration))
            time.sleep(params.duration / 1000.0)

        if params.telemetry and query_yes_no("Save Data?"):
            flashReadback(numSamples, params)

        repeatMenu(params)

    print "Done"

#Provide a try-except over the whole main function
# for clean exit. The Xbee module should have better
# provisions for handling a clean exit, but it doesn't.
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nRecieved Ctrl+C, exiting."
        shared.xb.halt()
        shared.ser.close()
    except Exception as args:
        print "\nGeneral exception:",args
        print "Attemping to exit cleanly..."
        shared.xb.halt()
        shared.ser.close()
        sys.exit()
    except serial.serialutil.SerialException:
        shared.xb.halt()
        shared.ser.close()
