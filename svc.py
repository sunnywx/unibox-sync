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
import traceback

import lib.logger

_log = lib.logger.Logger().get()

"""同步任务"""
def sync_worker(interval=60):
    import apps.Sync.sync as mod_sync
    ub_sync=mod_sync.UniboxSync()

    if interval is None:
        interval = 60

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
            _log.error('[svc]up sync failed: '+lib.logger.err_traceback())

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
            _log.error('[svc]down sync failed: '+lib.logger.err_traceback())

    sync_end = time.time()
    _log.logger.info('[svc]end sync worker, time elapsed '+ str(sync_end-sync_start) + 'sec\n')
    time.sleep(interval)


"""监控任务"""
def monitor_worker(interval=10):
    import apps.Monitor.monitor as mod_monitor
    ub_mon = mod_monitor.UniboxMonitor()
    if interval is None:
        interval = 10
    ub_mon.run()
    time.sleep(interval)

'''
check if svc is running, if master process is halt, so what?
check last sync timestamp, if period is beyond threshold value, force reload svc
'''
# todo
def check_svc_healthy():
    pass


class UniboxSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "UniboxSvc"
    _svc_display_name_ = "UniboxSvc"
    _svc_description_ = "a python powered win32 service built for sync, monitor and more by UniBox.Inc "

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.run = True
        self.logger = _log

    def SvcDoRun(self):
        self.logger.info("[svc]:uniboxSvc is starting")
        proc_pool=[]
        svc_interval = 10
        '''daemon process list'''
        fn_list = {
            'sync': (sync_worker, None),
            'monitor': (monitor_worker, None)
        }

        '''init process pool'''
        for n in fn_list.keys():
            proc_pool.append(multiprocessing.Process(name=n, target=fn_list[n][0], args=(fn_list[n][1],) ) )

        '''
        forking child process will have all the fd, sockets, thus will cause zombie connection,
        so multiprocess handler need fallback
        '''
        while self.run:
            try:
                for p in proc_pool:
                    self.logger.info('[svc]current pid='+str(os.getpid()))

                    '''process not started'''
                    if p._popen is None:
                        p.start()
                        self.logger.info('[svc]name='+str(p.name)+',pid='+str(p.pid)+' started')

                    if p.is_alive() is False:
                        '''process is stopped'''
                        self.logger.info('[svc]name='+str(p.name)+',pid='+str(p.pid)+' stopped')
                        p.terminate()
                        p.join(timeout=1)

                        '''remove stopped process, folk again'''
                        fn=p.name
                        proc_pool.remove(p)
                        new_proc=multiprocessing.Process(name=fn, target=fn_list[fn][0], args=(fn_list[fn][1],))
                        proc_pool.append(new_proc)
                        new_proc.start()
                        self.logger.info('[svc]'+fn+' folk again, pid='+str(new_proc.pid))

            except Exception, e:
                self.logger.error('[svc]'+lib.logger.err_traceback())

                # self.run=False
                '''reload svc'''

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
            self.logger.error('[svc]:'+self.svc_name + ' not installed')
            return False

        """open service control manager (SCM)"""
        """SC_MANAGER_ALL_ACCESS need root privilege"""
        try:
            self.scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
            """query unibox sync service"""
            self.hs = win32service.OpenService(self.scm, self.svc_name, win32service.SERVICE_ALL_ACCESS)
        except Exception, e:
            self.logger.error(str(e[1]) + ': ' + str(e[2]))

    def query(self, status):
        svcType, svcState, svcControls, err, svcErr, svcCP, svcWH = status
        is_running=False
        if svcState == win32service.SERVICE_STOPPED:
            self.logger.info("[svc] stopped")
        elif svcState == win32service.SERVICE_START_PENDING:
            self.logger.info("[svc] starting but pending")
            is_running=True
        elif svcState == win32service.SERVICE_STOP_PENDING:
            self.logger.info("[svc] stopping but pending")
        elif svcState == win32service.SERVICE_RUNNING:
            self.logger.info("[svc] running")
            is_running=True

        return is_running

    def getStatus(self):
        self.open()
        status = win32service.QueryServiceStatus(self.hs)
        running_state=self.query(status)
        self.close()
        return running_state

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
            self.logger.error(lib.logger.err_traceback())

    def stop(self):
        self.open()
        try:
            # win32service.ControlService(self.hs, win32service.SERVICE_CONTROL_STOP)
            """taskkill will kill all subprocess based on pythonservice.exe"""
            st=os.system('taskkill /f /im pythonservice.exe')
            if st==0:
                self.logger.info('svc stopped')
            else:
                os.system('net stop ' + self.svc_name)
            # self.getStatus()
        except Exception, e:
            self.logger.error(lib.logger.err_traceback())

    def restart(self):
        self.open()
        try:
            st = os.system('taskkill /f /im pythonservice.exe')
            if st != 0:
                os.system('net stop ' + self.svc_name)

            os.system('net start ' + self.svc_name)

        except Exception, e:
            self.logger.error(lib.logger.err_traceback())

"""used by subprocess or main module"""
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(UniboxSvc)