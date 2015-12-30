#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'a unibox monitor'

import psutil


class UniboxMonitor():
    """define data structure to keep monitor data"""
    ds = {
        'kiosk_id': ''  # 1
        , 'kiosk_ip': ''  # 由python获取，或者由服务端php获取
        , 'connected': ''  # True/False
        , 'mem_used': ''  # 1.0%
        , 'cpu_used': ''  # 10%
        , 'disk_used': ''  # 10%
        , 'rental_started': ''  # True/False
        , 'sync_started': ''  # True/False

    }

    def __init__(self):
        pass

    def get_process_list(self):
        plist = {}
        for p in psutil.process_iter():
            plist[p.name()] = p.pid
        return plist


    def get_machine_id(self):
        pass
        # kiosk_conf = parse_config(r'c:\ubkiosk\Kiosk.conf', '*')
        # return kiosk_conf['kioskid']


    def get_machine_ip(self):
        import socket

        return socket.gethostbyname(socket.gethostname())


if __name__ == '__main__':
    print 'starting unibox monitor program...\n'
    pass
    #
    # """get kiosk id"""
    # ds['kiosk_id'] = env.get_machine_id()
    #
    # """get machine public ip"""
    # ds['kiosk_ip'] = env.get_machine_ip()
    #
    # plist = get_process_list()
    # sync_glue = 'pythonservice.exe'
    # rental_glue = 'UDM_Rental.exe'
    # ds['sync_started'] = sync_glue in plist.keys()
    # ds['rental_started'] = rental_glue in plist.keys()
    #
    # ds['cpu_used'] = psutil.cpu_percent()
    # ds['mem_used'] = psutil.virtual_memory().percent
    # ds['disk_used'] = psutil.disk_usage('c:\\').percent
    #
    # """汇总监控信息"""
    # # print u'cpu used %s %%' % cpu_pct
    # # print u"memory used %s %%" % mem_pct
    # # print u"disk used %s %%" % disk_pct
    # print dict(ds)
    #
    # """模拟向服务器的一次请求"""

