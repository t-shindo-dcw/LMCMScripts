
import sys
import subprocess
import time
import re

def main():

  argvs = sys.argv
  argc = len(argvs)

  PIDString=argvs[1]
  Signal="-15"

  if argc > 2:
     Signal=argvs[2]

  #print ("DEBUG:KillTree: Root PID :",PIDString)
  KillCommandRecursively(PIDString,Signal)

def KillCommandRecursively(PIDString,Signal):

  ProcessKillMonitor=['ps','ax','-o','pid= ppid=']
#  print " ".join(ProcessKillMonitor)
  CommandPSResult=subprocess.check_output(ProcessKillMonitor)
  #print "DEBUG:KillTree: ps ax -o pid= ppid= :",CommandPSResult
  commandline=CommandPSResult.splitlines()

  ProcessKillCommand=['kill',Signal,PIDString]
#  print (ProcessKillCommand)
  try:
     subprocess.check_output(ProcessKillCommand)
  except:
     return

  ProcessKillMonitor=['kill','-0',PIDString]
  Result = ""
  while Result == "":
     try:
       Result=subprocess.check_call(ProcessKillMonitor)
     except:
       break
     time.sleep(0.1)

  print ("Killed ",PIDString,Signal)

  for PIDLine in commandline:
    #print ("DEBUG",PIDLine)
    PIDSet=re.split(" +", PIDLine.decode())
    if (len(PIDSet)>=3):
      if PIDSet[2] == PIDString :

        #print "DEBUG:KillTree:Call to kill "+PIDSet[1]
        KillCommandRecursively(PIDSet[1],Signal)
 



########################## MAIN #############################

if __name__ == "__main__":


# Initialize InportModule
	main()
