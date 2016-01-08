#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'common props and methods by unibox apps'

import util
import logger
import os
import sys
import inspect

log=logger.Logger().get()

def parse_kiosk_conf():
    kiosk_conf=util.parse_config(
        os.path.dirname(inspect.getfile(inspect.currentframe())) + '/../unibox.ini', 'UNIBOX')

    if type(kiosk_conf) is dict:
        extern_conf_file = kiosk_conf['ubkiosk_dir'] + 'Kiosk.conf'
        extern_conf = util.parse_config(extern_conf_file, '*')

        if type(extern_conf) is dict:
            kiosk_conf.update(extern_conf)
        else:
            kiosk_conf['kioskid']=0
            kiosk_conf['ownerid']=0
            log.error(kiosk_conf['kiosk_conf_file']+' config file error')
    else:
        return {}

    return kiosk_conf

"""export props"""
kiosk_conf = parse_kiosk_conf()
kiosk_id = kiosk_conf['kioskid']
owner_id = kiosk_conf['ownerid']
ubkiosk_dir = kiosk_conf['ubkiosk_dir']

if __name__ == '__main__':
    pass
