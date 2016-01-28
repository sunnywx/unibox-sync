#!/usr/bin/env python
# _*_ coding: gb2312 _*_
__author__ = 'wangxi'
__doc__ = 'a unibox monitor utility'

import sys
import os
import string
import datetime
import time
import inspect
import json

import apps

import lib.logger
import lib.util
import lib.sqlite
import lib.inet
import lib.unibox as unibox

import psutil

base_dir = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
logger = lib.logger.Logger('uniboxMonitor', base_dir).get()

class UniboxMonitor():
    """配置文件路径"""
    conf_file = base_dir + '/monitor_app.ini'

    sync_conf_file = os.path.abspath(base_dir + '/../Sync/sync_app.ini')

    """default monitor interval"""
    monitor_interval=10

    """监控配置项"""
    conf = {}

    """label if rental app init"""
    rental_init=False

    def __init__(self):
        """define data structure to keep monitor data"""
        self.ds = {
            'kiosk_id': ''
            , 'kiosk_ip': ''
            , 'mem_used': ''
            , 'cpu_used': ''
            , 'disk_free_size': ''
            , 'udm_rental_started': 0
            , 'udm_controller_started': 0
            , 'last_sync_time': 0
            , 'net_recv_bytes': 0  #网卡接收流量
            , 'net_send_bytes': 0   #网卡发送流量
            , 'last_boot_time': 0   #上次开机时间
        }

        conf = self.get_config()
        if len(conf) == 0:
            logger.error('invalid monitor config file')
            sys.exit(-1)

        self.conf = conf


    def get_config(self):
        conf = lib.util.parse_config(self.conf_file, 'MONITOR')
        if type(conf) is dict:
            if conf['monitor_interval'] == '' or conf['monitor_interval'] == 0:
                conf['monitor_interval'] = self.monitor_interval
            else:
                self.monitor_interval = int(conf['monitor_interval'])
            return conf

        return {}

    def get_process_list(self):
        plist = {}
        for p in psutil.process_iter():
            plist[p.name()] = p.pid
        return plist

    def get_kiosk_id(self):
        return unibox.kiosk_id

    def get_client_ip(self):
        import socket
        return socket.gethostbyname(socket.gethostname())

    def get_attrs(self):
        self.ds['kiosk_id'] = self.get_kiosk_id()
        self.ds['kiosk_ip'] = self.get_client_ip()

        plist = self.get_process_list()
        rental_alias= (self.conf['udm_rental'])[self.conf['udm_rental'].rfind('/')+1:]
        controller_alias = (self.conf['udm_controller'])[self.conf['udm_controller'].rfind('/')+1:]

        self.ds['udm_rental_started'] = 1 if rental_alias in plist.keys() else 0
        self.ds['udm_controller_started'] = 1 if controller_alias in plist.keys() else 0

        self.ds['last_boot_time'] = int(psutil.boot_time())

        """if white list proc is stopped, monitor should pull up those procs"""
        """
        udm_controller must be started before rental app
        """

        """TODO if rental app is halt, restart machine :( """
        """ monitor.unibox.dev is local dev server"""

        # if self.conf['server'] != 'http://monitor.unibox.dev':
        #     if self.ds['udm_controller_started'] == 1 and (int(time.time())-int(psutil.boot_time()) > 5*60):
        #         if self.ds['udm_rental_started'] == 0:
        #             logger.info('[Monitor]rental app halted, restart machine')
        #             os.system('shutdown /f /r /t 0')
        #             sys.exit(-1)

        # try:
        #     import subprocess
        #
        #     if self.ds['udm_controller_started'] == 0:
        #         logger.info('starting '+str(self.conf['udm_controller']))
        #         """os.system will block main python prog"""
        #         # os.system(self.conf['udm_controller'])
        #         subprocess.Popen(self.conf['udm_controller'])
        #
        #     if self.ds['udm_rental_started'] == 0:
        #         logger.info('starting '+str(self.conf['udm_rental']))
        #         # subprocess.call(self.conf['udm_rental'])
        #         subprocess.Popen(self.conf['udm_rental'])
        #
        # except Exception, e:
        #     logger.error(str(e))

        self.ds['cpu_used'] = '%d' % psutil.cpu_percent()
        self.ds['mem_used'] = '%d' % psutil.virtual_memory().percent
        self.ds['disk_free_size'] = '%d' % psutil.disk_usage('c:\\').free
        self.ds['last_sync_time'] = (lib.util.parse_config(self.sync_conf_file, 'SYNC'))['last_sync']

        net = psutil.net_io_counters()
        self.ds['net_recv_bytes'] = '%d' % net.bytes_recv
        self.ds['net_send_bytes'] = '%d' % net.bytes_sent

        return self.ds

    def stat(self):
        py_svc = 'pythonservice.exe'
        if py_svc in self.get_process_list():
            print u'UniboxSvc服务已启动'
            # pid_svc_daemon=self.get_process_list()[py_svc]
            # p=psutil.Process(pid=pid_svc_daemon)
            # print p
        else:
            print u'UniboxSvc服务已停止'

        self.endl()

        self.show_udm_proc()
        self.show_cpu()
        self.show_mem()
        self.show_disk()
        self.show_net()
        self.show_login_users()
        self.show_boot_time()

    def endl(self):
        print '---------------------------------------------\n'

    def show_udm_proc(self):
        print u'###检查UDM_Rental, UDM_Controller进程'
        plist = self.get_process_list()
        if 'UDM_Rental.exe' in plist.keys():
            print 'UDM_Rental 已启动'
        else:
            print 'UDM_Rental 已停止'

        if 'UDM_Controller.exe' in plist.keys():
            print 'UDM_Controller 已启动'
        else:
            print 'UDM_Controller 已停止'

        self.endl()

    def show_cpu(self):
        print u'###查看CPU信息'
        print u'CPU个数: %s' % psutil.cpu_count()
        print u'CPU times: %s' % str(psutil.cpu_times())
        print u'CPU使用率:% (最近4秒)'
        for x in range(4):
            print psutil.cpu_percent(interval=1)

        self.endl()

    def show_mem(self):
        print u'###查看内存信息'
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        print u'虚拟内存(bytes): %s' % str(vmem)
        print u'交换内存(bytes): %s' % str(swap)
        print u'内存总量: %.2f GB' % float(vmem.total / 1024.0 / 1024 / 1024)
        print u'内存利用率: %.2f %%' % vmem.percent
        self.endl()

    def show_disk(self):
        print u'###查看硬盘信息'
        c_disk = psutil.disk_usage('c:\\')
        print u'硬盘分区: %s' % str(psutil.disk_partitions('c\\'))
        print u'硬盘IO状况: %s' % str(psutil.disk_io_counters())
        print u'C盘使用状况: %s' % str(c_disk)
        print u'C盘大小: %.2f GB' % float(c_disk.total / 1024.0 / 1024 / 1024), \
            u', 剩余空间: %.2f GB' % float(c_disk.free / 1024.0 / 1024 / 1024)
        self.endl()

    def show_net(self):
        print u'###查看网络信息'
        net = psutil.net_io_counters()
        bytes_sent = '{0:.2f} Mb'.format(net.bytes_sent / 1024 / 1024)
        bytes_rcvd = '{0:.2f} Mb'.format(net.bytes_recv / 1024 / 1024)
        print u"网卡接收流量 %s 网卡发送流量 %s" % (bytes_rcvd, bytes_sent)
        self.endl()

    def show_boot_time(self):
        print u"机器上次启动时间 %s" % datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        self.endl()

    def show_login_users(self):
        print u'###查看当前系统登录用户'
        users_count = len(psutil.users())
        users_list = ",".join([u.name for u in psutil.users()])
        print u"当前有%s个用户，分别是 %s" % (users_count, users_list)
        self.endl()

    def run(self):
        print '[Monitor]sending beacon request', time.ctime()

        try:
            """模拟向服务器的beacon请求"""
            data = self.get_attrs()
            post_param = {
                "data": json.dumps(data)
            }
            req_url = self.conf['server'] + '/api/beacon?kioskId=' + data['kiosk_id']
            logger.info('[Monitor]req url: ' + req_url)

            server=self.conf['server']
            resp_body, resp_status = lib.inet.http_post(req_url, server, post_param)
            if len(resp_body) > 0:
                resp_body = json.loads(resp_body)

            print resp_body, resp_status, '\n'

        except Exception, e:
            logger.error(str(e))

if __name__ == '__main__':
    import time

    ub_mon = UniboxMonitor()
    # try:
    #     ub_mon.stat()
    # except Exception, e:
    #     logger.error(str(e))

    while True:
        ub_mon.run()

        time.sleep(10)


