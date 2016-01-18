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

import multiprocessing
# from multiprocessing import Process
# from multiprocessing import Pool

import win32serviceutil

import lib.logger

_log = lib.logger.Logger().get()

"""同步任务"""
def sync_worker(interval=60):
    import apps.Sync.sync as mod_sync
    ub_sync=mod_sync.UniboxSync()

    if interval is None:
        interval = 60

    last_sync_time=int(ub_sync.get_ini('last_sync'))
    down_sync_interval=int(ub_sync.get_ini('down_sync_interval'))
    up_sync_interval=int(ub_sync.get_ini('inventory_sync_interval'))
    svc_last_upsync=int(ub_sync.get_ini('svc_last_upsync'))
    svc_last_downsync=int(ub_sync.get_ini('svc_last_downsync'))

    sync_start=time.time()

    """priority: sync-inventory is higher than down-sync"""
    if sync_start - svc_last_upsync > up_sync_interval:
        try:
            ub_sync.sync_inventory()
            ub_sync.update_ini('svc_last_upsync')
        except Exception, e:
            _log.error('[sync_worker]up sync failed: '+str(e))

    if sync_start - svc_last_downsync > down_sync_interval:
        """execute down-sync"""
        try:
            ub_sync.sync_ad()
            ub_sync.sync_kiosk()
            ub_sync.sync_slot()
            ub_sync.sync_title()
            ub_sync.sync_movie()

            ub_sync.update_ini('svc_last_downsync')
        except Exception, e:
            _log.error('[sync_worker]down sync failed: '+str(e))

    sync_end = time.time()
    _log.logger.info('[UniboxSvc]end sync worker, time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    time.sleep(interval)

"""监控任务"""
def monitor_worker(interval=10):
    import apps.Monitor.monitor as mod_monitor
    ub_mon = mod_monitor.UniboxMonitor()
    if interval is None:
        interval = 10

    ub_mon.run()
    time.sleep(interval)


class UniboxSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "UniboxSvc"
    _svc_display_name_ = "Unibox Service"
    _svc_description_ = "Unibox Service for products of UniBox.Inc"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.run = True
        self.logger = _log

    def SvcDoRun(self):
        self.logger.info("[UniboxSvc]:service is starting")

        proc_pool=[]

        svc_interval = 10

        '''daemon process list'''
        fn_list = {
            'sync': (sync_worker, None),
            'monitor': (monitor_worker, None)
        }

        '''init process pool'''
        for n in fn_list.keys():
            proc_pool.append(multiprocessing.Process(name=n, target=fn_list[n][0], args=(fn_list[n][1],)))

        while self.run:
            try:
                for p in proc_pool:
                    '''process not started'''
                    if p._popen is None:
                        self.logger.info('name='+str(p.name)+',pid='+str(p.pid)+' not started, start it')
                        p.start()

                    if p.is_alive() is False:
                        '''process is stopped'''
                        self.logger.info('name='+str(p.name)+',pid='+str(p.pid)+' stopped, terminate it')
                        p.terminate()
                        p.join(timeout=1)

                        '''remove stopped process, folk again'''
                        fn=p.name
                        proc_pool.remove(p)
                        new_proc=multiprocessing.Process(name=fn, target=fn_list[fn][0], args=(fn_list[fn][1],))
                        self.logger.info(fn+' folk again, pid='+str(new_proc.pid))

                        proc_pool.append(new_proc)
                        new_proc.start()

            except Exception, err:
                self.logger.error(str(err))

            time.sleep(svc_interval)

    def SvcStop(self):
        self.logger.info("unibox service is stopping....")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.run = False


class SvcManager():
    def __init__(self, svc_name='UniboxSvc'):
        self.svc_name = svc_name
        self.logger=_log

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
            """taskkill will kill all subprocess based on pythonservice.exe"""
            st=os.system('taskkill /f /im pythonservice.exe')
            if st==0:
                print 'UniboxSvc is stopped'
            else:
                os.system('net stop ' + self.svc_name)
            # self.getStatus()
        except Exception, e:
            self.logger.error(e.message)
            sys.exit(-1)

    def restart(self):
        self.open()
        try:
            st = os.system('taskkill /f /im pythonservice.exe')
            if st != 0:
                os.system('net stop ' + self.svc_name)

            os.system('net start ' + self.svc_name)

        except Exception, e:
            self.logger.error(e.message)
            sys.exit(-1)

"""used by subprocess or main module"""
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(UniboxSvc)