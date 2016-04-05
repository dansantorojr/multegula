#!/usr/bin/python3
###########################################################
#Multegula - multegula.py                                 #
#Main Driver/Startup Script for Multegula                 #
#Armin Mahmoudi, Daniel Santoro, Garrett Miller, Lunwen He#
###########################################################

#######IMPORTS#######
import sys #Needs to be here before the path append.
import subprocess #Needed for system calls
import time #Needed to sleep
#####################

#Tells Python to search UI folder for functions as well.
sys.path.append('UI/')
from UI.multegulaUI import * #Import our UI functions

#Start PyBridge, and give it time to come up before continuing
PyBridge = subprocess.Popen(['go', 'run', 'Bridges/PyBridge.go'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(1)

#Start UI
runUI()
