#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'common props and methods by unibox apps'

import util
import logger
import os
import sys
import inspect
import string

log=logger.Logger().get()

ini_file=os.path.dirname(inspect.getfile(inspect.currentframe())) + '/../unibox.ini'

def parse_kiosk_conf():
    kiosk_conf=util.parse_config(ini_file, 'UNIBOX')

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

def get_app_version():
    # gen version num automatic
    ver=util.parse_config(ini_file, 'UNIBOX')

    if ver and ver['version'] != '':
        return ver['version']
    else:
        git_tags=os.popen('git tag').read().strip('\n')
        if git_tags:
            # get last tag
            lastest_ver=git_tags.split('\n')[-1]
            # save lastest_ver into extern file
            util.update_config(ini_file, {'version': lastest_ver}, 'UNIBOX')
            return lastest_ver

        else:
            # fake initial ver
            return 'v0.0.1'

def set_app_version():
    git_tags=os.popen('git tag').read().strip('\n')
    if git_tags:
        # get last tag
        lastest_ver=git_tags.split('\n')[-1]
        # save lastest_ver into extern file
        return util.update_config(ini_file, {'version': lastest_ver}, 'UNIBOX')

    return False

# based on git tag to compare two branchs version
# if local_ver is less than online_ver, need update it
def compare_version(local_ver, online_ver):
    local_ver=local_ver.lstrip('v').rstrip('\n')
    online_ver=online_ver.lstrip('v').rstrip('\n')
    log.info('checking py-ubx version, local_ver='+local_ver+', online_ver='+online_ver)

    return local_ver == online_ver

"""export props"""
kiosk_conf = parse_kiosk_conf()
kiosk_id = kiosk_conf['kioskid']
owner_id = kiosk_conf['ownerid']
ubkiosk_dir = kiosk_conf['ubkiosk_dir']

if __name__ == '__main__':
    pass
