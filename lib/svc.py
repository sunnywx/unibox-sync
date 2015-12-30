#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'wangXi'
__doc__ = 'unibox svc manipulation'

import win32service
import win32event
import sys
import os
import subprocess
import time

import win32serviceutil

import logger


class UniboxSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "UniboxSvc"
    _svc_display_name_ = "Unibox Service"
    _svc_description_ = "Unibox Service for products of UniBox.Inc"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.run = True
        self.logger = logger.logger

    def SvcDoRun(self):
        self.logger.info("unibox service is starting....")

        while self.run:
            self.logger.info('svc do something...')

            """service minimal sleep"""
            time.sleep(5)

    def SvcStop(self):
        self.logger.info("unibox service is stopping....")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.run = False


class SvcManager():
    def __init__(self, svc_name='UniboxSvc'):
        self.svc_name = svc_name
        self.logger=logger.logger

    def open(self):
        """check if service installed"""
        try:
            subprocess.check_output('SC QUERY ' + self.svc_name)
        except Exception, e:
            self.logger.error('[service]:'+self.svc_name + ' not installed')
            sys.exit(-1)

        """open service control manager (SCM)"""
        """SC_MANAGER_ALL_ACCESS need root privilege"""
        try:
            self.scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            """query unibox sync service"""
            self.hs = win32service.OpenService(self.scm, self.svc_name, win32service.SERVICE_ALL_ACCESS)
        except Exception, e:
            self.logger.error( str(e[1]) + ': ' + str(e[2]) )
            sys.exit(-1)

    def query(self, status):
        svcType, svcState, svcControls, err, svcErr, svcCP, svcWH = status

        if svcState == win32service.SERVICE_STOPPED:
            print "The service is stopped"
        elif svcState == win32service.SERVICE_START_PENDING:
            print "The service is starting"
        elif svcState == win32service.SERVICE_STOP_PENDING:
            print "The service is stopping"
        elif svcState == win32service.SERVICE_RUNNING:
            print "The service is running"

    def getStatus(self):
        self.open()
        status = win32service.QueryServiceStatus(self.hs)
        self.query(status)
        self.close()

    def close(self):
        win32service.CloseServiceHandle(self.hs)
        win32service.CloseServiceHandle(self.scm)

    def start(self):
        self.open()
        try:
            # win32service.StartService(self.hs, None)
            os.system('net start ' + self.svc_name)
            # self.getStatus()
        except Exception, e:
            self.logger.error(e.message)
            sys.exit(-1)

    def stop(self):
        self.open()
        try:
            # win32service.ControlService(self.hs, win32service.SERVICE_CONTROL_STOP)
            os.system('taskkill /f /im pythonservice.exe')
            os.system('net stop ' + self.svc_name)
            # self.getStatus()
        except Exception, e:
            self.logger.error(e.message)
            sys.exit(-1)

    def restart(self):
        self.open()
        try:
            os.system('taskkill /f /im pythonservice.exe')
            os.system('net stop ' + self.svc_name)
            os.system('net start ' + self.svc_name)
        except Exception, e:
            self.logger.error(e.message)
            sys.exit(-1)

"""used by subprocess or main module"""
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(UniboxSvc)