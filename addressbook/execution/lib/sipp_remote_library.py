#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable-all

"""
Sipp-Remote library
"""

#import pygst
#pygst.require("0.10")
#import gst
#import gobject
import logging
#import pygtk
#import gtk
from fabric.api import *
import signal
import os
import time
import glob
import datetime
from subprocess import Popen, PIPE
import subprocess
import shlex
import shutil
import re
import fileinput
import sys


class ContinuableError(AssertionError):
    """
    Класс ошибки. Если обнаружена ошибка, то выполняем тесты дальше
    """
    ROBOT_CONTINUE_ON_FAILURE = True

"""
Аргументы для передачи в тест кейс

"""
def validator(func):
    def wrapper(*args, **kwargs):
        validArgs=list()
        validKwargs=dict()
        for arg in args:
            if arg == 'None':
                validArgs.append(None)
            else:
                validArgs.append(arg)
        for key in kwargs:
            if kwargs[key] == 'None':
                validKwargs[key] = None
            else:
                validKwargs[key] = kwargs[key]
        func(*validArgs, **validKwargs)
    return wrapper


class SippRemoteLibrary(object):
    """
    Класс запуска sipp
    """

    def __init__(self):
        self.current_filename = os.path.basename(__file__)

    @validator
    def setup(self, scenario_dir, sipp_username, sipp_password, sipp_cgpn, sipp_domen,
              sipp_i, dest_ip_port, sipp_p="5060", sipp_m="1",
              sipp_r=None, sipp_rp=None, sipp_timeout=None, sipp_3pcc=None, sipp_mp=None, expires_time=None, sipp_mi=None, sipp_rtp_echo=None):


        """
        Функция установки значений переменных.
        Они далее будут использоваться
        для формирования команды для запуска sipp
        """
        #sipp_r="1", sipp_rp="1"

        self.sipp_set = {}
        self.sipp = 'sipp'  # Путь до sipp
        self.scenario_dir = scenario_dir
        self.sipp_au = sipp_username
        self.sipp_ap = sipp_password
        self.sipp_trace_err = True
        self.sipp_trace_msg = True
        self.sipp_trace_log = True
        self.sipp_trace_screen = True
        self.sipp_aa = True
        self.sipp_p = sipp_p
        self.sipp_mp = sipp_mp
        self.sipp_m = sipp_m
        
        self.sipp_r = sipp_r
        self.sipp_rp = sipp_rp
        self.sipp_timeout = sipp_timeout

        self.sipp_mi = sipp_mi
        self.sipp_rtp_echo = sipp_rtp_echo

        self.sipp_skip_rlimit = True
        self.sipp_i = sipp_i
        self.sipp_s = None
        self.sipp_3pcc = sipp_3pcc


        if sipp_cgpn:
            self.sipp_set['cgpn'] = sipp_cgpn
        if sipp_domen:
            self.sipp_set['domen'] = sipp_domen
        if expires_time:
            self.sipp_set['expires_time'] = expires_time

        self.dest_ip_port = dest_ip_port

        print "*INFO* Setup success"


        # Переменные, используемые в сценариях они прописаны в init.txt


    def set_cdpn(self, sipp_cdpn):
        """Задаём номер вызываемого абонента"""
        self.sipp_s = sipp_cdpn
        print "*INFO* Set cdpn success"
        print "*DEBUG* cdpn: %s" % self.sipp_s

    def run_scenario(self, scenario_name, log_error=None, log_message=None, log_log=None):
         """Функция запуска sipp с определенным сценарием"""
         log = "log"
         sbc_log = "sbc_log"
         self.mvsip_log_send = "mvsip_log_send"
         self.mvsip_log_receive = "mvsip_log_receive"
         self.scenario_dir = os.path.join(self.scenario_dir, scenario_name)  # Путь до сценария
         print "self.scenario_dir = %s" % self.scenario_dir 
         self.scenario_log_dir = os.path.join(self.scenario_dir, log)  # Путь до логов
         self.scenario_sbc_log_dir = os.path.join(self.scenario_dir, sbc_log)  # Путь до sbc логов
         if not os.path.exists(self.scenario_log_dir):
             os.makedirs(self.scenario_log_dir)
         if not os.path.exists(self.scenario_sbc_log_dir):
             os.makedirs(self.scenario_sbc_log_dir)
#        self.scenario_dir = os.path.join('/home/papachappa/robot/back_sbc_tests/sipp_remote_library/scenario/', scenario_name)  # Путь до сценария
#        self.scenario_log_dir = os.path.join('/home/papachappa/robot/back_sbc_tests/sipp_remote_library/scenario/%s' % scenario_name, log)  # Путь до логов
#        self.scenario_sbc_log_dir = os.path.join('/home/papachappa/robot/back_sbc_tests/sipp_remote_library/scenario/%s' % scenario_name, sbc_log)  # Путь до sbc логов

         print "LOG DIR is %s" % self.scenario_log_dir
         self.sipp_sf = os.path.join(self.scenario_dir, "scenario.xml")
#        self.sipp_inf = os.path.join(self.scenario_dir, "%s" % scenario_csv)
         self.sipp_error_file = os.path.join(self.scenario_log_dir, "%s" % log_error)
         self.sipp_message_file = os.path.join(self.scenario_log_dir, "%s" % log_message)
         self.sipp_log_file = os.path.join(self.scenario_log_dir, "%s" % log_log)

        #self.sipp_log_counts_file = os.path.join(self.scenario_log_dir, "%s" % log_counts)

         self.sipp_total_command = self._generate_sipp_total_command()
         print "*DEBUG* Sipp total command: %s" % self.sipp_total_command

#        #create sbc_log directory
#        if not os.path.exists(self.scenario_sbc_log_dir):
#          os.makedirs(self.scenario_sbc_log_dir)    

         if os.path.isfile(self.sipp_error_file): os.remove(self.sipp_error_file)
         if os.path.isfile(self.sipp_message_file): os.remove(self.sipp_message_file)
         if os.path.isfile(self.sipp_log_file): os.remove(self.sipp_log_file)
         for file in os.listdir(self.scenario_dir):
            if "_screen.log" in file: os.remove(os.path.join(self.scenario_dir, file))

        #Deleting csv file
         os.chdir(self.scenario_dir)
         filelist = [ f for f in os.listdir(self.scenario_dir) if f.endswith("counts.csv") ]
         for f in filelist:
           if os.path.isfile(f):
            os.remove(f)

        # self.scenario_subprocess = Popen(self.sipp_total_command, shell=True, stdin=PIPE, stderr=PIPE, stdout=None)
         total_command = shlex.split(self.sipp_total_command)
         devnull = open(os.devnull, 'w')
         err = open(self.sipp_error_file, 'w')
         senv = os.environ
         senv["TERM"] = 'xterm'
         #print '*DEBUG* %s' % total_command
         self.scenario_subprocess = Popen(total_command, stdin=devnull, stderr=err, stdout=devnull, env=senv)
         # subproc_out, subproc_err = self.scenario_subprocess.communicate()
         print "*INFO* Run success"

    def waiting_for_stop_scenario(self, wait_time):
        """
        Функция ожидания окончания выполнения сценария sipp.
        Если не было ответа в течении wait_time,
        убиваем процесс и возбуждаем ошибку.
        Если был возвращен код отличный от rc = 1, то также возбуждаем ошибку
        """
        wait_time = int(wait_time)
        start_time = time.time()
        while True:
            time.sleep(0.01)
            rc = self.scenario_subprocess.poll()
            elapsed_time = (time.time() - start_time)
            if rc == None and elapsed_time > wait_time:
                

		pid = self.scenario_subprocess.pid
                print "*DEBUG* Current pid %s" % pid
                time.sleep(1)
                print "*DEBUG* Try kill sipp's processes pids"
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()

                raise ContinuableError("Subprocess not ended on %s seconds, can't get return code, try check sipp logs!!!" % wait_time)
            elif rc != None:
                break

        print "*DEBUG* Return code: %s" % rc

        if rc == 0:
            time.sleep(1)
            self._kill_pids(self.scenario_dir)
            print "*INFO* Subprocess ended success, rc: %s" % rc
        else:
            if rc in [1, 97, 99, -1, -2]:
                time.sleep(1)
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()
                raise ContinuableError("Subprocess not ended correctly, sipp error! Check sipp logs! rc: %s" % rc)
            else:
                print "*INFO* stdout:\n%s\nstderr:\n%s" % (self.scenario_subprocess.communicate())
                time.sleep(1)
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()
                raise ContinuableError("Subprocess not ended correctly, bash error! Check stdout and stderr of subprocess! rc: %s" % rc)



    def waiting_for_stop_scenario_fail(self, wait_time):
        
        wait_time = int(wait_time)
        start_time = time.time()
        while True:
            time.sleep(0.01)
            rc = self.scenario_subprocess.poll()
            elapsed_time = (time.time() - start_time)
            if rc == None and elapsed_time > wait_time:
                pid = self.scenario_subprocess.pid
                print "*DEBUG* Current pid %s" % pid
                time.sleep(1)
                print "*DEBUG* Try kill sipp's processes pids"
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()

                raise ContinuableError("Subprocess not ended on %s seconds, can't get return code, try check sipp logs!!!" % wait_time)
            elif rc != None:
                break

        print "*DEBUG* Return code: %s" % rc

        if rc in [0, 1, 97, 99]:
            time.sleep(1)
            self._kill_pids(self.scenario_dir)
            print "*INFO* Subprocess ended success, rc: %s" % rc
        else:
            if rc in [-1, -2]:
                time.sleep(1)
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()
                raise ContinuableError("Fatal Sipp Error! Subprocess not ended correctly, sipp error! Check sipp logs! rc: %s" % rc)
            else:
                print "*INFO* stdout:\n%s\nstderr:\n%s" % (self.scenario_subprocess.communicate())
                time.sleep(1)
                self._kill_pids(self.scenario_dir)
                self._kill_child_pids()
                raise ContinuableError("Subprocess not ended correctly, bash error! Check stdout and stderr of subprocess! rc: %s" % rc)
    
    def moving_csv(self):
        os.chdir(self.scenario_dir)
        for filename in os.listdir("."):
          if filename.endswith("counts.csv"):
            os.rename(filename, "counts%s.csv" % self.sipp_au)
        if os.path.exists("%s/counts%s.csv" % (self.scenario_log_dir, self.sipp_au)):
            os.remove("%s/counts%s.csv" % (self.scenario_log_dir, self.sipp_au))
        shutil.move("%s/counts%s.csv" % (self.scenario_dir, self.sipp_au), "%s" % self.scenario_log_dir)

   

    """
    Далее идут функции для попытки успешного завершения подвисшего процесса sipp.
    Пока вроде работает )
    """

    def kill_sipp(self):
        #  SIGUSR1 30,10,16   depends on system, in my case it is 16 and 30   
        #  SIGUSR2 31,12,17   depends on system, in my case it is 31   
        #   linux usage  kill -SIGNUM PID

        pid = self.scenario_subprocess.pid
        print "*DEBUG* Current pid %s" % pid
        print "*DEBUG* Try kill sipp's processes pids"
        self._kill_individual_pid(self.scenario_log_dir)
        #self._kill_child_pids()


    def _kill_individual_pid(self, process):
        self._get_pids(process)
        self._check_pids_count(process)
        print '*DEBUG* Start kill pids'
        print '*DEBUG* Executing pids:\n%s' % self.pids_data
        pids = self.pids_data.rstrip('\n').split('\n')
        print '*DEBUG* Pids in list: %s' % pids
        if int(self.pids_count) > 0 and pids[-1] != '':
            for pid in pids:
                print '*DEBUG* Kill %s' % pid
                # os.kill(int(pid), signal.SIGKILL)
                os.kill(int(pid), signal.SIGTERM)  #31

 
    def _kill_pids(self, process):
        self._get_pids(process)
        self._check_pids_count(process)
        print '*DEBUG* Start kill pids'
        print '*DEBUG* Executing pids:\n%s' % self.pids_data
        pids = self.pids_data.rstrip('\n').split('\n')
        print '*DEBUG* Pids in list: %s' % pids
        if int(self.pids_count) > 0 and pids[-1] != '':
            for pid in pids:
                print '*DEBUG* Kill %s' % pid
                # os.kill(int(pid), signal.SIGKILL)
                os.kill(int(pid), signal.SIGUSR2)

    def _kill_child_pids(self):
        self._get_child_pids()
        self._check_child_pids_count()
        child_pids = self.child_pids_data.rstrip('\n').split('\n')
        if int(self.child_pids_count) > 0 and child_pids[-1] != '':
            print '*DEBUG* Found child pids %s. Try to kill' % child_pids
            for pid in child_pids:
                print '*DEBUG* Kill %s' % pid
                os.kill(int(pid), signal.SIGKILL)

        print '*DEBUG* Success kill all pids'

    def _get_pids(self, process):
        command = ("ps afx | grep %s | grep -v grep | awk '{print $1}'"
                   % process)
        self.pids_data = subprocess.check_output([command], shell=True)

    def _check_pids_count(self, process):
        command = ("ps afx | grep %s | grep -v grep | wc -l" % process)
        self.pids_count = subprocess.check_output([command], shell=True)

    def _get_child_pids(self):
        command = ("ps afx | grep sipp | grep -v grep |" +
                   " grep -v %s | awk '{print $1}'") % self.current_filename
        self.child_pids_data = subprocess.check_output([command], shell=True)

    def _check_child_pids_count(self):
        command = ("ps afx | grep sipp | grep -v grep |" +
                   " grep -v %s | wc -l") % self.current_filename
        self.child_pids_count = subprocess.check_output([command], shell=True)

    def logs(self):
        """Функция для считывания лог файлов sipp."""
        files = glob.glob(os.path.join(self.scenario_dir, 'scenario_*_screen.log'))

        if len(files) == 0:
            print "*INFO* sipp screen file doesn't exists"
        elif len(files) > 1:
            print "*INFO* there is more than one sipp screen file!!!"
        else:
            print "*INFO* sipp screen file:\n%s" % open(files[0]).read()

        if os.path.isfile(self.sipp_message_file):
            print "*DEBUG* sipp message file:\n%s" % open(self.sipp_message_file).read()
        else:
            print "*DEBUG* sipp message file doesn't exists"

        if os.path.isfile(self.sipp_error_file):
            print "*DEBUG* sipp error file:\n%s" % open(self.sipp_error_file).read()
        else:
            print "*DEBUG* sipp error file doesn't exists"

        if os.path.isfile(self.sipp_log_file):
            print "*DEBUG* sipp log file:\n%s" % open(self.sipp_log_file).read()
        else:
            print "*DEBUG* sipp log file doesn't exists"

    def _generate_sipp_total_command(self):
        """Функция формирующая команду для запуска sipp."""
        
        sipp_total_command = self.sipp
        sipp_total_command += ' -sf ' + self.sipp_sf
#	sipp_total_command += ' -inf ' + self.sipp_inf
        sipp_total_command += ' -error_file ' + self.sipp_error_file
        sipp_total_command += ' -message_file ' + self.sipp_message_file
        sipp_total_command += ' -log_file ' + self.sipp_log_file
        if self.sipp_trace_err: sipp_total_command += " -trace_err"
        if self.sipp_trace_msg: sipp_total_command += " -trace_msg"
        if self.sipp_trace_log: sipp_total_command += " -trace_logs"
        sipp_total_command += " -trace_counts"
        
        if self.sipp_trace_screen: sipp_total_command += " -trace_screen"
        if self.sipp_aa: sipp_total_command += " -aa"
        if self.sipp_skip_rlimit: sipp_total_command += " -skip_rlimit"
        sipp_total_command += ' -au ' + self.sipp_au
        sipp_total_command += ' -ap ' + self.sipp_ap
        sipp_total_command += ' -p ' + self.sipp_p
        if self.sipp_3pcc: sipp_total_command += ' -3pcc ' + self.sipp_3pcc
        if self.sipp_mp: sipp_total_command += ' -mp ' + self.sipp_mp
        sipp_total_command += ' -m ' + self.sipp_m
        
        if self.sipp_r: sipp_total_command += ' -r ' + self.sipp_r
        if self.sipp_rp: sipp_total_command += ' -rp ' + self.sipp_rp
        if self.sipp_timeout: sipp_total_command += ' -timeout ' + self.sipp_timeout        

        if self.sipp_mi: sipp_total_command += ' -mi ' + self.sipp_mi
        if self.sipp_rtp_echo: sipp_total_command += ' -rtp_echo'

        if self.sipp_s: sipp_total_command += ' -s ' + self.sipp_s
        for key in self.sipp_set:
          sipp_total_command += ' -set %s %s' % (key, self.sipp_set[key])
        sipp_total_command += ' -i ' + self.sipp_i
        sipp_total_command += ' ' + self.dest_ip_port
	sipp_total_command += ' -nostdin'

        return sipp_total_command

    def compare(self):
        "Функция для анализа содержимого лог-файла"
        f = open(str(self.sipp_log_file), 'r')
        self.content = f.read()
        if "From: <sip:anonymous@anonymous.in" in self.content and "Contact: <sip:anonymous@" in self.content:
            print "*INFO* Service AON Forbid (CLIR) work success"
            print "*DEBUG* %s" % self.content
        else:
            raise ContinuableError("Service AON don't work!!!")
            print "*DEBUG* Service AON Forbid (CLIR) don't work! %s" % self.content

    def init_socket(self):
        f = open(str(self.sipp_log_file))
        content = f.read()
        rem_ip = re.search('remote_ip: .*', content)
        self.remote_ip = str(rem_ip.group(0).split(': ')[1])
        rem_port = re.search('remote_port: .*', content)
        self.remote_port = int(rem_port.group(0).split(': ')[1])
        loc_ip = re.search('local_ip: .*', content)
        self.local_ip = str(loc_ip.group(0).split(': ')[1])
        loc_port = re.search('local_port: .*', content)
        self.local_port = int(loc_port.group(0).split(': ')[1])
        print self.remote_ip, self.remote_port, self.local_port
        return self.remote_ip, self.remote_port, self.local_port


    def check_file(self, file_f, *words):
#        file_path = os.path.abspath(file_f)
        datafile = file(file_f)
  
        for word in words:
          datafile.seek(0)
          if word in datafile.read():
             print "*INFO* Logs contain a %s section. All is good" % word   
          else:
             raise AssertionError("Logs does not contain a %s section. Error" % word)


    def replace_string(self, file_f,str1,str2):
        f = fileinput.FileInput(file_f, inplace=True)
        for line in f:
            s = line.replace(str1, str2)
            sys.stdout.write(s)

    def compare_weights(self, file_f):
        with open('%s' % file_f, 'r') as inF:
         for line in inF:
           if re.search("([0-9]+;){21}", line):
              s = line[60:].split(";")
              s = max(s)
        print "*INFO* %s" % s
        return s  

#    def manipulation(self, component, action, host_ip):
 #       with settings(user='root', password='elephant', host_string=host_ip, warn_only="False"):
  #          out = run('grep FLASH /usr/protei/Protei-MKD/MKD/profiles.vpbx/1/Users/2000.cfg')
   #         return out
  
    
    def import_sbc_logs(self, remote_sbc_dir, remote_host):
        with settings(user='root', password='elephant', host_string=remote_host, warn_only="False"):
             #get('%s/logs/alarm_cdr.log' % remote_sbc_dir, self.scenario_sbc_log_dir)
             #get('%s/logs/warning.log' % remote_sbc_dir, self.scenario_sbc_log_dir)
             #get('%s/logs/sbc_diagnostic.log' % remote_sbc_dir, self.scenario_sbc_log_dir)
             #get('%s/logs/sbc_diagnostic_warning.log' % remote_sbc_dir,  self.scenario_sbc_log_dir)
             #get('%s/logs/sip_transport.log' % remote_sbc_dir,  self.scenario_sbc_log_dir)
             #get('%s/logs/sbc_cdr.log' % remote_sbc_dir,  self.scenario_sbc_log_dir) 
             #get('%s/logs/com_trace.log' % remote_sbc_dir,  self.scenario_sbc_log_dir) 
             #get('%s/logs/com_info.log' % remote_sbc_dir,  self.scenario_sbc_log_dir) 
             get('%s/logs/*.log' % remote_sbc_dir,  self.scenario_sbc_log_dir)


    def import_mvsip_logs(self, remote_mvsip_dir, remote_host):
         self.scenario_mvsip_log_dir_send = os.path.join(self.scenario_dir, self.mvsip_log_send)  # Путь до mvsip логов
         if not os.path.exists(self.scenario_mvsip_log_dir_send):
             os.makedirs(self.scenario_mvsip_log_dir_send)
         self.scenario_mvsip_log_dir_receive = os.path.join(self.scenario_dir, self.mvsip_log_receive)  # Путь до mvsip логов
         if not os.path.exists(self.scenario_mvsip_log_dir_receive):
             os.makedirs(self.scenario_mvsip_log_dir_receive)
         with settings(user='root', password='elephant', host_string=remote_host, warn_only="False"):
             get('%s/0/logs/*' % remote_mvsip_dir, self.scenario_mvsip_log_dir_send)
             get('%s/1/logs/*' % remote_mvsip_dir, self.scenario_mvsip_log_dir_receive)


#a = SippRemoteLibrary()
#print a.setup("6001", "1234567890", "6001", "linksys.sip.pbx", "192.168.100.6", "5556", "5060", "1", "None", "None", "None", "None", "None", "None", "None", "None")
#a._generate_sipp_total_command()

#print s

        

if __name__ == '__main__':
   import sys
   from robotremoteserver import RobotRemoteServer
   RobotRemoteServer(SippRemoteLibrary(), *sys.argv[1:])
