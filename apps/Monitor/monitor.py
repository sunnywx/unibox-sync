#!/usr/bin/env python
# _*_ coding: utf-8 _*_
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

import psutil

base_dir = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
logger = lib.logger.Logger('uniboxMonitor', base_dir).get()


class UniboxMonitor():
    """配置文件路径"""
    conf_file = base_dir + '/monitor_app.ini'

    """监控配置项"""
    conf = {}

    def __init__(self):
        """define data structure to keep monitor data"""
        self.ds = {
            'kiosk_id': ''  # integer
            , 'kiosk_ip': ''  # 由python获取，或者由服务端php获取
            , 'connected': False
            , 'mem_used': ''  # 1.0%
            , 'cpu_used': ''  # 10%
            , 'disk_free_size': ''  # 10%
            , 'udm_rental_started': False
            , 'udm_controller_started': False
        }

        conf = self.get_config()
        if len(conf) == 0:
            logger.error('invalid monitor config file')
            sys.exit(-1)

        self.conf=conf


    def get_config(self):
        conf = lib.util.parse_config(self.conf_file, 'MONITOR')
        if type(conf) is dict:
            return conf
        return {}

    def get_process_list(self):
        plist = {}
        for p in psutil.process_iter():
            plist[p.name()] = p.pid
        return plist

    def get_kiosk_id(self):
        kiosk_conf = lib.util.parse_config(self.conf['kiosk_conf'], '*')
        return kiosk_conf['kioskid']

    def get_client_ip(self):
        import socket
        return socket.gethostbyname(socket.gethostname())

    def get_attrs(self):
        self.ds['kiosk_id']=self.get_kiosk_id()
        self.ds['kiosk_ip']=self.get_client_ip()

        plist = self.get_process_list()
        self.ds['udm_rental_started'] = self.conf['udm_rental'] in plist.keys()
        self.ds['udm_controller_started'] = self.conf['udm_controller'] in plist.keys()

        self.ds['cpu_used'] = '%d' % psutil.cpu_percent()
        self.ds['mem_used'] = '%d' % psutil.virtual_memory().percent
        self.ds['disk_free_size'] = '%d' % psutil.disk_usage('c:\\').free
        return self.ds



if __name__ == '__main__':
    import time
    while True:
        logger.info( time.ctime()+': [Monitor]sending beacon request')
        ub_mon=UniboxMonitor()

        """模拟向服务器的beacon请求"""
        data=ub_mon.get_attrs()
        post_param = {
            "data": json.dumps(data)
        }
        req_url=ub_mon.conf['server']+'/index.php?c=home&m=beacon&kioskId='+data['kiosk_id']
        logger.info('req url: '+req_url)

        resp_body, resp_status,resp_code = lib.inet.http_post(req_url, ub_mon.conf['server'], post_param)
        if len(resp_body)>0:
            resp_body = json.loads(resp_body)

        print resp_body, resp_status, resp_code

        logger.info(time.ctime()+': end cycle')

        time.sleep(2)

