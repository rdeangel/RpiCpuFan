#!/usr/bin/env python3
# Author: Rocco De Angelis

import os
import sys
import RPi.GPIO as GPIO
from time import sleep
import getopt
import logging, logging.handlers

class RpiPin(object):

    """Set a specific Raspberry Pi GPIO OUTPUT Pin ON or OFF.
    """
    def __init__(self, pin):
    
        self.pin = pin
		
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.setwarnings(False)
        GPIO.output(pin, False)
        return(None)

    #Check pin status
    def getPin(self):
        pinState = GPIO.input(self.pin)
        if pinState == 1:
            return "ON"
        elif pinState == 0:
            return "OFF" 
        else:
            return pinState
 
    #Set pin to ON or OFF
    def setPin(self, mode):
        GPIO.output(self.pin, mode)
        return()
    
	#Clenup pin configuration
    def cleanUP(self):
        GPIO.cleanup()

def main(argv):
    arg_help = "usage: RpiCpuFan.py --on-temp=<on-temp> --off-temp=<off-temp> --ping=<pin> --interval=<interval sec> -v --local-log= --syslog= -a (-h|--help)"

    arg_help_extended = '''usage: RpiCpuFan.py --on-temp=<on-temp> --off-temp=<off-temp> --ping=<pin> --interval=<interval sec> -v --local-log= --syslog= -a (-h|--help)

      --on-temp=       max temperature before the fan is turned ON (default 55)
      --off-temp=      minimum temperature before fan is turned OFF (default 50)
      --pin=           GPIO pin which turns the fan on and off (default 18 sec)
  -i  --interval=      temperature check interval (default 5 sec)
  -v                   verbose output that shows temperature, when fan is turned on or off
  -l  --local-log=     log fan activity messages locally
      --syslog=        log fan activity messages to a specific syslog server
  -a                   this opion can only be used with --local-log or --syslog or both,
                       and enables loggin of the temperature when fan is ON on a set interval
  -h, --help           help and extended help
'''
    try:
        opts, args = getopt.getopt(argv,"vl:ah:",["on-temp=","off-temp=","pin=","interval=","local-log=","syslog=","help"])
    except getopt.GetoptError:
        print (arg_help)
        sys.exit(2)

    #Defaul values if arguments below are not specified at start
    onTemp = 55 #Default Higher temperature in Celsius after which we trigger the fan
    offTemp = 50 #Default Lower temperature the fan is turned off after a trigger
    pin = 18 #Default GPIO pin ID used
    interval = 5 #Default interval of seconds used
    verbose = False #Default verbose logging off
    localLog = False #Default localLog off
    localLogFile = "/var/log/RpiCpuFan.log" # Default localLogFile
    syslog = False #Default syslog off
    syslogIP = "" #Default empty syslog value
    logAlwaysWhenON = False #Default on-logging off

    #Extract and set arguments and options
    for opt, arg in opts:
        if opt in ("--on-temp"):
            onTemp = int(arg)
        if opt in ("--off-temp"):
            offTemp = int(arg)
        if opt in ("--pin"):
            pin = int(arg)
        if opt in ("--interval"):
            interval = int(arg)
        if opt in ("-v"):
            verbose = True
        if opt in ("-l", "--local-log"):
            localLog = True
            if str(arg) != "":
                localLogFile = str(arg)
        if opt in ("--syslog"):
            syslog = True
            syslogIP = str(arg)
        if opt in ("-a"):
            if localLog or syslog:
                logAlwaysWhenON = True
            else:
                print (arg_help_extended)
                sys.exit()
        elif opt in ("-h", "--help"):
            print (arg_help_extended)
            sys.exit()

    datefmtSet = "%d-%m-%Y %H:%M:%S"
    formatterConsoleMsg = "%(message)s"
    formatterFileMsg = "%(asctime)s - RpiCpuFan.py - %(levelname)s - %(message)s"
    formatterSyslogMsg = "RpiCpuFan.py %(message)s"

    consoleLogger = logging.getLogger('RpiCpuFan_console')
    consoleLogger.setLevel(logging.INFO)
    consoleFormatter = logging.Formatter(formatterConsoleMsg)
    cl = logging.StreamHandler(sys.stdout,)
    cl.setFormatter(consoleFormatter)
    consoleLogger.addHandler(cl)

    fileLogger = logging.getLogger('RpiCpuFan_file')
    fileLogger.setLevel(logging.INFO)
    fileFormatter = logging.Formatter(formatterFileMsg, datefmt=datefmtSet)
    fl = logging.FileHandler(localLogFile, 'a')
    fl.setFormatter(fileFormatter)
    fileLogger.addHandler(fl)

    syslogLogger = logging.getLogger('RpiCpuFan_syslog')
    syslogLogger.setLevel(logging.INFO)
    syslogFormatter = logging.Formatter(formatterSyslogMsg)
    sl = logging.handlers.SysLogHandler(address=(syslogIP,514))
    sl.setFormatter(syslogFormatter)
    syslogLogger.addHandler(sl)

    #Get CPU Temp
    def getCPUtemp():
        res = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
        temp =(res.replace("temp=","").replace("'C\n",""))
        return temp
    
    #Controle Fan ON and OFF
    def fanActivate(mode):
        cpufan.setPin(mode)
        fanActionChangeMsg = "Fan was %s and pin changed to: %s"
        if mode == True:
            if verbose == True:
                consoleLogger.info(fanActionChangeMsg, "activated", "ON")
            if localLog == True:
                fileLogger.info(fanActionChangeMsg, "activated", "ON")
            if syslog == True:
                syslogLogger.info(fanActionChangeMsg, "activated", "ON")
        if mode == False:
            if verbose == True:
                consoleLogger.info(fanActionChangeMsg, "deactivated", "OFF")
            if localLog == True:
                fileLogger.info(fanActionChangeMsg, "deactivated", "OFF")
            if syslog == True:
                syslogLogger.info(fanActionChangeMsg, "deactivated", "OFF")
		
    #Temperature trigger based on temperature
    def checkTempTrigger():
        CPUtemp = float(getCPUtemp())
        pinStatus = cpufan.getPin()
        fanStatusMsg = "Fan is %s, CPU Temperature is %s'C"
        if verbose == True:
            consoleLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)
        if localLog == True:
            if pinStatus == "ON" and logAlwaysWhenON:
                fileLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)        
        if syslog == True:
            if pinStatus == "ON" and logAlwaysWhenON:
                syslogLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp) 
        if (CPUtemp>onTemp) and (pinStatus == "OFF"):
            fanActivate(True)
            if logAlwaysWhenON is False:
                if localLog == True:
                    fileLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)
                if syslog == True:
                    syslogLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)
        elif (CPUtemp<=offTemp) and (pinStatus == "ON"):
            fanActivate(False)
            if logAlwaysWhenON is False:
                if localLog == True:
                    fileLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)
                if syslog == True:
                    syslogLogger.info(fanStatusMsg, cpufan.getPin(), CPUtemp)
        return()

    try:
        cpufan = RpiPin(pin)
        onCPUTempMsg = "Fan ON CPU Temperature set to: {0}'C".format(onTemp)
        offCPUTempMsg = "Fan OFF CPU Temperature set to: {0}'C".format(offTemp)
        fanPinMsg = "Fan GPIO pin is set to: {0}".format(pin)
        intervalMsg = "CPU temperature check and Fan trigger interval set to: {0}".format(interval)
        if verbose == True:
            consoleLogger.info("-----------------------------------------------")
            consoleLogger.info("RpiCpuFan.py starting...")
            consoleLogger.info(onCPUTempMsg)
            consoleLogger.info(offCPUTempMsg)
            consoleLogger.info(fanPinMsg)
            consoleLogger.info(intervalMsg)
            print ("\n")
        if localLog == True:
            fileLogger.info("-----------------------------------------------")
            fileLogger.info("RpiCpuFan.py starting...")
            fileLogger.info(onCPUTempMsg)
            fileLogger.info(offCPUTempMsg)
            fileLogger.info(fanPinMsg)
            fileLogger.info(intervalMsg)
        if syslog == True:
            syslogLogger.info("RpiCpuFan.py starting...")
            syslogLogger.info(onCPUTempMsg)
            syslogLogger.info(offCPUTempMsg)
            syslogLogger.info(fanPinMsg)
            syslogLogger.info(intervalMsg)
        while True:
            checkTempTrigger() #Temperature check and trigger
            sleep(interval)
    except KeyboardInterrupt: #Trap a CTRL+C keyboard interrupt 
        cpufan.cleanUP() #Resets GPIO pins used by the program

if __name__ == "__main__":
    main(sys.argv[1:])

