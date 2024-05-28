#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
### Scheduler task 
###
###                     Kyowa system   Ver0.9
###
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

from apscheduler.triggers import cron
from socket import error as socket_error

import datetime
import time
import socket
import sys
import os
import copy
import subprocess
import base64
import threading
import signal
import logging


host = '192.168.2.100' # IP address
port = 10020 # Port number
ID_Max=65536

class Stack:
  def __init__(self,Line,CallerStack):
     self.BeginLine=Line
     self.CurrentLine=Line
     self.NextLine=Line+1
     self.LoopCount=0
     self.Parent=CallerStack
     self.Task=None
  def SetTask(self,Task):
     self.Task=Task

class Task:
  def __init__(self,Line,Stack):
     self.CurrentStack=Stack
     self.BeginLine=Line


ScheduleLines = []
Tasks = []
RunningTaskContext = None
NumberandIndexes = {}
LabelandIndexes = {}
Scheduler = BackgroundScheduler()
LOCK = threading.Lock()
RunningSubProcess = None
TerminationRequest=False
WorkerThread=None

###  Load from Task file
def main():

   argvs = sys.argv  # コマンドライン引数を格納したリストの取得
   argc = len(argvs) # 引数の個数
   if (argc < 2):   # 引数が足りない場合は、その旨を表示
      print ('Usage: # python %s \"TaskFile.txt\" PIDFile [IP] [port] ' % argvs[0])
      quit()         # プログラムの終了

   # Interrupt handler
   signal.signal(signal.SIGINT, AbortHandler)

   global host 
   global port
   global ScheduleLines
   global NumberandIndexes

   ### Prepare socket
   host = socket.gethostbyname(socket.gethostname())
   try :
      host = os.popen('ip addr show lo').read().split("inet ")[1].split("/")[0]
   except IndexError:
      pass
   print ("Detected host ip address  : %s" % host)
   TaskFile=argvs[1] # Task file
   if (argc >= 4):
     host = argvs[3] # IP address
   if (argc >= 5):
      port = int(argvs[4]) # Port number

   #PIDファイル作成
   pidFile="/var/tmp/lmc/lmcscheduler.pid"
   if (argc >= 3):
     if (argvs[2]!=""):
        pidFile=argvs[2]

   pid = os.getpid()
   with open(pidFile, 'w') as f:
      f.write(str(pid))

   #TaskFile="TaskFile.txt"
   TaskFilePointer = open(TaskFile, "r")

   ### ファイルからタスクを読み出し
   ID=0
   for line in TaskFilePointer:
     # skip comment
     if r"#" in line[0:1]:
        continue
     #print "ScheduleLine original ",line
     # Order :  Task : Enable : Time : Command : Comment
     strippedline=line.rstrip(" ")
     if len(strippedline) == 0:
        continue
     ScheduleLine=CustomizedSplit(strippedline,':')
     #print "ScheduleLine ",ScheduleLine
     if len(ScheduleLine) < 5:
        continue
     if len(ScheduleLine) < 6:
        ScheduleLine.append(" ")
     ScheduleLine.append(str(ID))
     ScheduleLines.append(ScheduleLine)
     ID = ID + 1
   TaskFilePointer.close()
 
   # デフォルトログ指定
   log = logging.getLogger('apscheduler.executors.default')
   log.setLevel(logging.INFO)  # DEBUG

   fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
   h = logging.StreamHandler()
   h.setFormatter(fmt)
   log.addHandler(h)


   # 値の初期化
 
   # タスクスケジューラ登録
 
   TaskLine=0
   for SchedulerLineEntry in ScheduleLines:
      #print (u"DEBUG: Task line %d" % TaskLine)
      #print "DEBUG",SchedulerLineEntry
      if len(SchedulerLineEntry) < 6:
          continue
      Valid=SchedulerLineEntry[1]
      if ( Valid!="Enable" ):
          continue
      SchedulerLineCopy=copy.copy(SchedulerLineEntry)
      if (SchedulerLineCopy[2]=='cron'):
         SchedulerLineCopy[3]=ParseTimingString(SchedulerLineCopy,TaskLine)
         EntryToSchedulerEvent(SchedulerLineCopy,TaskLine)
      elif (SchedulerLineCopy[2]=='interval'):
         SchedulerLineCopy[3]=ParseTimingString(SchedulerLineCopy,TaskLine)
         EntryToSchedulerEvent(SchedulerLineCopy,TaskLine)
      elif (SchedulerLineCopy[2]=='date'):
         ParseDateTimeString(SchedulerLineCopy,TaskLine)
         #SchedulerLineCopy[3]=ParseEndTimingString(SchedulerLineCopy,TaskLine)
         #EntryToSchedulerEvent(SchedulerLineCopy,TaskLine)
      elif (SchedulerLineCopy[2]=='now'):
         # Top priority
         ParseTimingString(SchedulerLineCopy,TaskLine)
         EntryNewTaskFromInterrupt(TaskLine)
      elif (TaskLine==0):
         ParseTimingString(SchedulerLineCopy,TaskLine)
         EntryNewTask(TaskLine)
      else:
         ParseTimingString(SchedulerLineCopy,TaskLine)

      # Entry line number for call target
      ID=SchedulerLineCopy[0]
      NumberandIndexes[ID]=TaskLine

      TaskLine+=1

   # Default task started
   EventFunc("")

   Scheduler.start()
   print("Scheduler started")
   while True:
      time.sleep(60)

   return

def AbortHandler(signal, frame):
   #停止要求
   global TerminationRequest
   global RunningSubProcess
    
   print("Abort requested. Terminate child processes.")

   RunningTaskContext=None
   TerminationRequest=True
   ResetTask()
   sys.exit(0)  # TODO temporary comment out



##
##  Scheduler parser section
##

def EntryToSchedulerEvent(SchedulerLineEntry,TaskLine):
      ### NormalScedulerEventを登録
      global Scheduler

      SchedulerTiming=SchedulerLineEntry[3]
      # apscheduler timing description
      TaskParameterList=CustomizedSplit(SchedulerTiming,',')
      #print ("TaskParameterList : ")
      #print (TaskParameterList)
      if len(TaskParameterList) == 1:
         TaskParameterList=[SchedulerTiming]

      TaskParameters={}
      for TaskParameterEquation in TaskParameterList:
         # 時間指定を変換 'date' 'minute' ...等
         TaskParameter=CustomizedSplit(TaskParameterEquation,'=')
         TaskParameterValue=TaskParameter[1].lstrip('\'')
         TaskParameterValue=TaskParameterValue.rstrip('\'')
         if TaskParameterValue.isdigit():
            TaskParameterValue=int(TaskParameterValue)
         TaskParameters[TaskParameter[0]]=TaskParameterValue
      TaskParameters["func"]=EventFunc
      TaskParameters["trigger"]=SchedulerLineEntry[2]
      TaskParameters["args"]=[str(TaskLine)]
      # [SchedulerTask[4]]は登録しない。
      TaskParameters["name"]="LMC_"+str(TaskLine)
      TaskParameters["id"]=SchedulerLineEntry[0]
      # 1 minute interval
      TaskParameters["misfire_grace_time"]=60
      print ("Entry scheduler head task ",TaskLine)
      print ("DEBUG : Task lists : ")
      print (TaskParameters.keys())
      print ("DEBUG : Task Values : ")
      print (TaskParameters.values())
      try:
         Scheduler.add_job(**TaskParameters)
      except TypeError as e:
         print ("Scheduler syntax error : line ",SchedulerLineEntry[0])
         pass
 

def ParseTimingString(SchedulerLineEntry,CurrentLine):
   global LabelandIndexes
   TimingStrings=SchedulerLineEntry[3]
   TaskString=SchedulerLineEntry[5]
   ID=SchedulerLineEntry[0]
   TimingList=CustomizedSplit(TimingStrings,',')
   ResultTimingList=[]
   for timing in TimingList:
       TimingEquation=CustomizedSplit(timing,'=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           print ("DEBUG TimingName: ",TimingName)
           # Ignore scheduler description
           if (TimingName==r'reset'):
               continue
           elif (TimingName==r'loopcount'):
               continue
           elif (TimingName==r'targetlabel'):
               continue
           elif (TimingName==r'label'):
               LabelandIndexes[TimingEquation[1]]=CurrentLine
               print ("DEBUG LabelandIndexes: ",TimingEquation[1],CurrentLine)
               continue
           else:
               ResultTimingList.append(timing)

   ResultString=",".join(ResultTimingList)
   print ("DEBUG ResultString: ",ResultString)
   return ResultString

def ParseEndTimingString(SchedulerLineEntry,CurrentLine):
   TimingStrings=SchedulerLineEntry[3]
   TaskString=SchedulerLineEntry[5]
   ID=SchedulerLineEntry[0]
   TimingList=CustomizedSplit(TimingStrings,',')
   ResultTimingList=[]
   for timing in TimingList:
       TimingEquation=CustomizedSplit(timing,'=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           print ("DEBUG TimingName: ",TimingName)
           if (TimingName==r'end_time'):
               EntryEndTimeTask(CurrentLine,TaskString,ID,TimingEquation[1])
               ResultTimingList.append(TimingEquation)
           #elif (TimingName==r'reset'):
               #
           else:
               ResultTimingList.append(timing)
 
   ResultString=",".join(ResultTimingList)
   print ("DEBUG ResultString: ",ResultString)
   return ResultString


def ParseDateTimeString(SchedulerLineEntry,CurrentLine):
   TimingStrings=SchedulerLineEntry[3]
   TaskString=SchedulerLineEntry[5]
   ID=SchedulerLineEntry[0]
   TimingList=CustomizedSplit(TimingStrings,',')
   ResultTimingList=[]
   BeginTime=None
   EndTime=None
   EndTimeEquation=None
   for timing in TimingList:
       TimingEquation=CustomizedSplit(timing,'=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           TimingValue=TimingEquation[1].lstrip('\'')
           TimingValue=TimingValue.rstrip('\'')
           print ("DEBUG TimingName: ",TimingName)
           if (TimingName==r'run_date'):
               BeginTime=datetime.datetime.strptime(TimingValue, '%Y-%m-%d %H:%M:%S')
               ResultTimingList.append(timing)
               print ("Begin time : " , BeginTime.isoformat())
           elif (TimingName==r'end_time'):
               EndTimeEqution=TimingValue
               EndTime=datetime.datetime.strptime(TimingValue, '%Y-%m-%d %H:%M:%S')
               print ("End time : " , EndTime.isoformat())
           else:
               ResultTimingList.append(timing)
 
   if (BeginTime==None):
       return 
   ResultString=",".join(ResultTimingList)
   print (" Scheduler_date CommandLineString " , ResultString)
   SchedulerLineEntry[3]=ResultString
   CurrentTime= datetime.datetime.now()

   if (CurrentTime>BeginTime):
       if (EndTime==None) or (CurrentTime<EndTime):
            print (" date is now active. Activate now")
            EntryNewTaskFromInterrupt(CurrentLine)
            return
   if (EndTime!=None):
       print (" Entry end timing ",EndTimeEquation)
       EntryEndTimeTask(CurrentLine,TaskString,ID,EndTimeEquation)

   print (" Entry start timing ")
   EntryToSchedulerEvent(SchedulerLineEntry,CurrentLine)


def EntryEndTimeTask(CurrentLine,TaskString,ID,EndTime):
   ### Timer限定 Timer終了ScedulerEventを登録
   global ID_Max
   TaskParameters={}
   TaskParameters["run_date"]=EndTime
   TaskParameters["func"]=EndTimeFunc
   TaskParameters["trigger"]='date'
   TaskParameters["args"]=[str(CurrentLine)]
   TaskParameters["name"]="LMC_end_"+str(CurrentLine)
   TaskParameters["id"]=ID_Max+str(ID)
   #1 minute interval
   TaskParameters["misfire_grace_time"]=60
   print ("Entry EndTime task ",CurrentLine)
   print ("DEBUG : Task lists : ")
   print (TaskParameters.keys())
   print ("DEBUG : Task Values : ")
   print (TaskParameters.values())
   try:
      Scheduler.add_job(**TaskParameters)
   except TypeError as e:
      print ("Scheduler syntax error : line ",str(ID))
      pass

def CustomizedSplit(InputLine,Separator):

  InsideQuotation=False
  InsideQuotation2=False
  ResultList=[]
  ResultListItem = ""
  for char in InputLine:
     if char=='\'':
       if InsideQuotation:
           InsideQuotation=False
       else:
           InsideQuotation=True
     if char=='"':
       if InsideQuotation2:
           InsideQuotation2=False
       else:
           InsideQuotation2=True

     if InsideQuotation==False:
        if InsideQuotation2==False:
           if char==Separator:
              ResultList.append(ResultListItem)
              ResultListItem=""
              continue
     ResultListItem+=char

  if (ResultListItem!=""):
     ResultList.append(ResultListItem)
  return ResultList

##
##  Event interrupt section
##

def EventFunc(SchedulerLineString):
      ### TimerEventからここに到達する
      global RunningTaskContext
      global RunningSubProcess
      global WorkerThread
      if (SchedulerLineString!=""):
         SchedulerLineNumber=int(SchedulerLineString)
         print ("Entry next schedule line from event interrupt %d" % SchedulerLineNumber)

         EntryNewTaskFromInterrupt(SchedulerLineNumber)

         if (ParseTaskHead(SchedulerLineNumber)):
             ### 実行中スレッドのリセットを実行
             if (RunningTaskContext!=None):
                RunningTaskContext=None
                ResetTask()

      if (RunningTaskContext == None):
          # 実行中タスクが無いならば、即座にQueueから取り出してThread生成。
          IssueNextTask()
          print ("Start task thread ")
          WorkerThread=threading.Thread(target=TaskThread, args=[])
          WorkerThread.start()

def EndTimeFunc(SchedulerLineString):
      SchedulerLineNumber=int(SchedulerLineString)
      print ("End task from event interrupt %d" % SchedulerLineNumber)
      RemoveSpecifiedTask(SchedulerLineNumber)

##
##  Main execution thread
##

def TaskThread():
     ###LMCなどの実際の制御ループはこのスレッドで実行する。
     global RunningTaskContext
     global ScheduleLines
     global Lock
     global TerminationRequest
     while (True):
         if (TerminationRequest):
            break

         IssueNextTask()

         if (RunningTaskContext==None):
             print ("No next task.")
             #TaskThread ends
             break

         CurrentLine=RunningTaskContext.CurrentLine
         print ("Evaluating current line : %d" % CurrentLine)
         #TaskLineのコマンドを実行すべきかを判断する。NextLineへの代入も行われる。 
         Result=ParseCurrentLine(CurrentLine)

         BranchResult=True
         if (Result):
            print ("Confirmed. Current task line is ready to execute: line %d" % CurrentLine)
            ### RunningContextは書き換わっている可能性はある
            RunningTask=ScheduleLines[CurrentLine]
            BranchResult=CommandFunc(RunningTask[4])
            print ("DEBUG : IfBranchExecuted : ",BranchResult)


         if (RunningTaskContext!=None):
            # Check Branch result
            if (BranchResult):
                ParseCurrentLineForConditionalCall(CurrentLine,BranchResult)
 
         if (RunningTaskContext!=None):
            ### Go to next line
            RunningTaskContext.CurrentLine=RunningTaskContext.NextLine


     print ("Task ended")

def CommandFunc(message):

    #message=message.encode('utf-8')
   if message==None or message=="":
     return True
   if r"lmcCmd_" in message:
     ### CommandServerの呼び出し
     LMCCommand(message)
     return True
   else:
     ### カレントディレクトリの実行ファイルを起動する
     #try:
        message=message.replace(chr(0x1f), " ")
        decodestrArray=message.split(' ')
        ExecutingFile=os.path.basename(decodestrArray[0])
        ExecutingFile=os.path.join(os.getcwd(),ExecutingFile)
        decodestrArray[0]=ExecutingFile
        print ("Remote execution command : " , decodestrArray)
        RunningSubProcess=subprocess.Popen(decodestrArray, shell=False)
        ExecutionResult=RunningSubProcess.wait()
        RunningSubProcess=None

        if ExecutionResult==0:
          return True
        return False

     #except OSError as e:
     #   print e
     #   if (e.args[0]==2):
     #     #"[OSError: [Errno 2] No such file or directory"
     #     print ("Remote process error.")
     #     time.sleep(5)
     #     pass
     #   else:
     #     raise e

def LMCCommand(message):
     # try
        print ('IP : %s ' % host)
        print ('Port : %d ' % port)
        print ('Send message : %s ' % message)

        message=base64.b64encode(message.encode('utf-8'))

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client.connect((host, port)) 

        client.send(message)

        client.send("\n".encode('utf-8'))

        while True:
             response = client.recv(4096)
             if response == '':
                  break
             returndata=response.decode('utf-8')
             print (returndata)
             if 'Ready.' in returndata:
                  break

        client.close()
        print ("Command 1 line ended")
     # 以下の例外処理は、キャッチはできるが動作ができない。
     #except IOError as e:
     #   print e
     #   if (e.args[0]==111):
     #     #"[Errno 111] Connection refused"
     #     print "Remote connection error."
     #     time.sleep(5)
     #     pass
     #   else:
     #    print "Raise exceotion again."
     #    raise e

def ResetTask():
     print ("Reset running task")
     if (RunningSubProcess!=None):
         RunningSubProcess.terminate()
     else:
         LMCCommand("lmcCmd_abort")

##
##  Command parser on running section
##
def ParseTaskHead(CurrentTaskLine):
   global ScheduleLines
   global RunningTaskContext
   SchedulerTask=ScheduleLines[CurrentTaskLine]

   #print (SchedulerTask)
   if len(SchedulerTask) < 6:
       return False
   TimingStrings=SchedulerTask[3]
   print ("DEBUG TimingStrings : ",TimingStrings)
   TimingList=TimingStrings.split(',')
   CallTargetLine=-1
   for timing in TimingList:
       print ("DEBUG timing entry: ",timing)
       TimingEquation=timing.split('=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           print ("DEBUG TimingName: ",TimingName,TimingEquation[1])
           if (TimingName==r'reset'):
               # reset 
               print ("Reset previous task")
               return True
   return False



def ParseCurrentLine(CandidateTaskLine):
    # Commandに応じて、次に実行すべきラインを決定する。 
    # -1の場合は、実行せずにスキップする。
    # 現在の読み出しラインはRunningTaskContext.CurentLineに入っている。

    # 通常のCMDであれば実行するために値をそのまま返す
    # Loop命令であれば、冒頭に帰る。ループスタックを利用。
    # Eventであれば、そこで終了
    global ScheduleLines
    global RunningTaskContext

    LoopHeadLine=RunningTaskContext.BeginLine
    print ("DEBUG : LoopHeadLine %d" % LoopHeadLine)
    print ("DEBUG : Parse Next Task line %d" % CandidateTaskLine)
    if (CandidateTaskLine<0):
       return False
    print ("DEBUG : len(ScheduleLines) %d" % len(ScheduleLines))

    if (len(ScheduleLines)<=CandidateTaskLine):
       print ("No next task.Task ended.")
       return ExecuteReturn()

    RunningTaskContext.NextLine=CandidateTaskLine+1

    SchedulerTask=ScheduleLines[CandidateTaskLine]
    #print (SchedulerTask)
    if len(SchedulerTask) < 6:
       return False

    Result=True
    TaskName=SchedulerTask[2]
    if (TaskName=='cron'):
       if (LoopHeadLine!=CandidateTaskLine):
          print ("Reached to next event. Task ended. ")
          ExecuteReturn()
          Result=False
    elif (TaskName=='interval'):
       if (LoopHeadLine!=CandidateTaskLine):
          print ("Reached to next event. Task ended. ")
          ExecuteReturn()
          Result=False
    elif (TaskName=='date'):
       if (LoopHeadLine!=CandidateTaskLine):
          print ("Reached to next event. Task ended. ")
          ExecuteReturn()
          Result=False
    elif (TaskName=='now'):
       if (LoopHeadLine!=CandidateTaskLine):
          print ("Reached to next event. Task ended. ")
          ExecuteReturn()
          Result=False
    elif (TaskName=='sub'):
       if (LoopHeadLine!=CandidateTaskLine):
          print ("Reached to next subtask. Task ended. ")
          ExecuteReturn()
          Result=False
    elif (TaskName=='loop'):
       # Loopで戻る。回数はない
       print ("Reached to Loop command.")
       #ParseTaskTimingLoop(SchedulerTask[3])
       Result=True
    elif (SchedulerTask[2]=='call'):
       print ("Reached to Call command.")
       #ParseTaskTimingCall(SchedulerTask[3])
       Result=True
    else:
       # 通常実行
       Result=True

    Valid=SchedulerTask[1]
    if ( Valid!='Enable' ):
       print ("Task diasbled Go to next task")
       Result=False

    return Result

def ParseCurrentLineForConditionalCall(CandidateTaskLine,BranchResult):
    global ScheduleLines
    global RunningTaskContext
    SchedulerTask=ScheduleLines[CandidateTaskLine]

    #print (SchedulerTask)
    if len(SchedulerTask) < 6:
       return False

    TaskName=SchedulerTask[2]
    if (TaskName=='loop'):
       # Loopで戻る。回数はない
       print ("Reached to Loop command. Condition approved.")
       ParseTaskTimingLoop(SchedulerTask[3])
       Result=True
    elif (SchedulerTask[2]=='call'):
       print ("Reached to Call command.Condition approved.")
       ParseTaskTimingCall(SchedulerTask[3])
       Result=True


def ParseTaskTimingLoop(TimingStrings):
   global RunningTaskContext
   TimingList=TimingStrings.split(',')
   LoopTargetLine=-1

   if (RunningTaskContext!=None):
      LoopTargetLine=RunningTaskContext.BeginLine

   # Evaluate loop count
   for timing in TimingList:
       TimingEquation=timing.split('=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           print ("DEBUG TimingName: ",TimingName)
           if (TimingName==r'loopcount'):
               LoopTargetLine=EvaluateLoopCount(int(TimingEquation[1]))
   if (LoopTargetLine<0):
       # Loop end
       print ("DEBUG LoopTarget return: ")
       ExecuteReturn()
   elif (RunningTaskContext!=None):
       # Go to loop head
       RunningTaskContext.NextLine=LoopTargetLine


def ParseTaskTimingCall(TimingStrings):
   global LabelandIndexes
   global NumberandIndexes
   TimingList=TimingStrings.split(',')
   CallTargetLine=-1
   for timing in TimingList:
       TimingEquation=timing.split('=')
       if (len(TimingEquation)==2):
           TimingName=TimingEquation[0]
           print ("DEBUG TimingName: ",TimingName,TimingEquation[1])
           if (TimingName==r'targetlabel'):
               CallTargetLine=LabelandIndexes.get(TimingEquation[1],-1)

   if (CallTargetLine>=0):
        ExecuteCall(CallTargetLine)
   else:
        print ("DEBUG : Ignore call target :" , TimingEquation[1])

##
##  Task manager section
##
def EntryNewTask(HeadLineOfTask):
    global Tasks
    global Lock
    if LOCK.acquire(True):
       TaskInsertPlace=len(Tasks)
       i=0
       for CurrentTask in Tasks:
          if (CurrentTask.BeginLine==HeadLineOfTask):
              break
          if (CurrentTask.BeginLine>HeadLineOfTask):
              TaskInsertPlace=i
              break
          i=i+1
       if (TaskInsertPlace>=0):
          NewContext=Stack(HeadLineOfTask,None)
          NewTask=Task(HeadLineOfTask,NewContext)
          NewContext.SetTask(NewTask)
          Tasks.insert(TaskInsertPlace,NewTask)
          print ("Add task : line "+str(HeadLineOfTask))
       LOCK.release()

def EntryNewTaskFromInterrupt(HeadLineOfTask):
    global Tasks
    global Lock
    if LOCK.acquire(True):
       NewContext=Stack(HeadLineOfTask,None)
       NewTask=Task(HeadLineOfTask,NewContext)
       NewContext.SetTask(NewTask)
       Tasks.insert(0,NewTask)
       print ("Add task into front : line "+str(HeadLineOfTask))
       LOCK.release()

def IssueNextTask():
    global Lock
    global RunningTaskContext
    # 登録済みのタスクを行の先頭から発行する。 RunningTaskContextはNoneのはず。
    if LOCK.acquire(True):
       RunningTaskContext==None
       if (len(Tasks)>0):
           RunningTask=Tasks[0]
           RunningTaskContext=RunningTask.CurrentStack
           print ("Issue task : line "+str(RunningTaskContext.CurrentLine))
       LOCK.release()

def EvaluateLoopCount(NumberOfLoops):
    # Check loop
    global Lock
    global RunningTaskContext
    if (RunningTaskContext==None):
       return -1
    if LOCK.acquire(True):
       RunningTaskContext.LoopCount=RunningTaskContext.LoopCount+1
       LoopCount=RunningTaskContext.LoopCount
       BeginLine=RunningTaskContext.BeginLine
       LOCK.release()
    print ("DEBUG : EvaluateLoop "+str(LoopCount)+ " until "+ str(NumberOfLoops))
    if (LoopCount>=NumberOfLoops):
       print ("DEBUG : Loop end")
       return -1
    return BeginLine

def ExecuteCall(CallTarget):
    # Call呼び出し到達
    global Lock
    global RunningTaskContext
    print ("Execute call"+str(CallTarget))
    if LOCK.acquire(True): 
       if (RunningTaskContext!=None):
          RunningTaskContext.NextLine=RunningTaskContext.CurrentLine+1
          NewStack=Stack(CallTarget,RunningTaskContext)
          NewStack.NextLine=CallTarget
          NewStack.SetTask(RunningTaskContext.Task)
          RunningTaskContext.Task.CurrentStack=NewStack
          RunningTaskContext=NewStack
       LOCK.release()

def ExecuteReturn():
    # Code末端到達。つまり、Returnでスタックを上に戻す
    # あるいは別のタスクを発行する。
    global Lock
    global RunningTaskContext
    print ("Execute return")
    if LOCK.acquire(True): 
       if RunningTaskContext.Parent==None:
          # スタックなし
          RemoveTask(RunningTaskContext.Task)
          RunningTaskContext=None
       else: 
          # スタックを上へ
          CurrentLine=RunningTaskContext.CurrentLine
          RunningTaskContext=RunningTaskContext.Parent
          RunningTaskContext.Task.CurrentStack=RunningTaskContext

       LOCK.release()

def RemoveTask(RemovingTask):
    # 現在待機中のTaskを、Tasksから削除
    global Tasks
    global Lock
    global RunningTaskContext
    Tasks.remove(RemovingTask)
    print ("Task was removed")

def RemoveSpecifiedTask(RemovingTaskBeginLine):
    # BeginLineで指定されたタスクを消去する。 
    global RunningTaskContext
    if LOCK.acquire(True): 
       for Task in Tasks:
          if (Task.BeginLine==RemovingTaskBeginLine):
             Tasks.remove(Task)
             print ("Task was removed from interrupt")
             break
       if (RunningTaskContext!=None):
          if (RunningTaskContext.BeginLine==RemovingTaskBeginLine):
              RunningTaskContext=None
       LOCK.release()

########################## MAIN #############################

if __name__ == "__main__":
        main()
