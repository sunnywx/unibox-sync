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
import zlib
from zipfile import *

import urllib2

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
        try:
            git_tags=os.popen('git tag').read().strip('\n')

            if git_tags:
                # get last tag
                lastest_ver=git_tags.split('\n')[-1]
                # save lastest_ver into extern file
                util.update_config(ini_file, {'version': lastest_ver}, 'UNIBOX')
                return lastest_ver
        except Exception, e:
            # fake initial ver
            return 'v0.0.1'

def set_app_version():
    try:
        git_tags=os.popen('git tag').read().strip('\n')
        if git_tags:
            # get last tag
            lastest_ver=git_tags.split('\n')[-1]
            # save lastest_ver into extern file
            return util.update_config(ini_file, {'version': lastest_ver}, 'UNIBOX')

    except Exception, e:
        return False

# based on git tag to compare two branchs version
# if local_ver is less than online_ver, need update py-ubx
# -1 local < online
# 0 local == online
# 1 local > online
def compare_version(local_ver, online_ver):
    suffix=['alpha', 'beta', 'rc']

    local_ver=local_ver.lstrip('v').rstrip('\n')
    online_ver=online_ver.lstrip('v').rstrip('\n')
    log.info('checking py-ubx version, local_ver='+local_ver+', online_ver='+online_ver)

    if local_ver == online_ver:
        return 0

    local_num=local_ver[:5]
    online_num=online_ver[:5]
    if local_num[0] < online_num[0]:
        return -1
    elif local_num[2] < online_num[2]:
        return -1
    elif local_num[4] < online_num[4]:
        return -1
    else:
        if local_ver.find('-') != -1:
            suf_local=local_ver.split('-')[-1]
            if online_ver.find('-') != -1:
                # suffix must in ['alpha','beta','rc']
                suf_online=online_ver.split('-')[-1]
                if suf_local in suffix and suf_online in suffix:
                    return -1 if suf_local<suf_online else 1
                else:
                    # do nothing
                    return 0
            else:
                return -1


def backup_files(from_path, to_path, clean_dst=True):
    import shutil
    if os.path.exists(to_path):
        if clean_dst is True:
            shutil.rmtree(to_path)

    shutil.copytree(from_path, to_path)

'''copytree 函数的回调'''
def ignore_list(src, names):
    pass

'''ubx程序回滚机制'''
def rollback():
    pass

def checking_update():
    upd_svr=kiosk_conf['update_server'].strip('\'')     # careful trail slash :(

    if upd_svr[-1] != '/':
        upd_svr += '/'

    req_online_ver=upd_svr+'update.txt'

    try:
        resp = urllib2.urlopen(req_online_ver)
        online_ver=resp.read()

        local_ver=get_app_version()

        if compare_version(local_ver, online_ver) < 0:
            # download zip-ball
            zip_file='py-ubx-'+get_app_version()+'.zip'

            import lib.inet as inet

            log.info('start downloading zip file: ' +upd_svr+zip_file)
            inet.download_file(upd_svr+zip_file)

            zip_ubx = ZipFile(util.sys_tmp(None, zip_file), 'r')
            # name_list=zip_ubx.namelist()
            # print zip_ubx.extract('.gitignore')

            extract_folder=util.sys_tmp(filename='ubx-update')

            log.info('[updater] extract latest files to '+extract_folder)
            zip_ubx.extractall(extract_folder)

            """backup original conf file and logs"""
            orig_bak_dir=util.sys_tmp(filename='ubx-orig-bak')
            if not os.path.exists(orig_bak_dir):
                os.mkdir(orig_bak_dir)

            import shutil
            base_dir=os.path.dirname(ini_file)

            """bak sync logs"""
            log.info('[updater] backup original sync logs')
            backup_files(os.sep.join([base_dir, 'apps/Sync/log']), os.sep.join([orig_bak_dir, 'sync_log']))
            backup_files(os.sep.join([orig_bak_dir, 'sync_log']), os.sep.join([extract_folder, 'apps/Sync/log']))


            """bak sync ini"""
            log.info('[updater] backup original sync ini')
            shutil.copy2(os.sep.join([base_dir, 'apps/Sync/sync_app.ini']), os.sep.join([orig_bak_dir, 'sync_app.ini']))
            shutil.copy2(os.sep.join([orig_bak_dir, 'sync_app.ini']), os.sep.join([extract_folder, 'apps/Sync/sync_app.ini']))


            """bak monitor logs"""
            log.info('[updater] backup original monitor logs')
            backup_files(os.sep.join([base_dir, 'apps/Monitor/log']), os.sep.join([orig_bak_dir, 'monitor_log']))
            backup_files(os.sep.join([orig_bak_dir, 'monitor_log']), os.sep.join([extract_folder, 'apps/Monitor/log']))


            """bak monitor ini"""
            log.info('[updater] backup original monitor ini')
            shutil.copy2(os.sep.join([base_dir, 'apps/Monitor/monitor_app.ini']), os.sep.join([orig_bak_dir, 'monitor_app.ini']))
            shutil.copy2(os.sep.join([orig_bak_dir, 'monitor_app.ini']), os.sep.join([extract_folder, 'apps/Monitor/monitor_app.ini']))


            """bak ubx logs"""
            log.info('[updater] backup original ubx logs')
            backup_files(os.sep.join([base_dir, 'log']), os.sep.join([orig_bak_dir, 'ubx_log']))
            backup_files(os.sep.join([orig_bak_dir, 'ubx_log']), os.sep.join([extract_folder, 'log']))

            import traceback
            import svc

            svc_mgr=svc.SvcManager()
            svc_mgr.stop()

            dst='c:\\py-ubx'
            dst_bak=dst+'-bak'
            if os.path.exists(dst):
                '''rename original py-ubx dir as py-ubx-bak as a rollback dir'''
                os.rename(dst, dst_bak)

            try:
                backup_files(extract_folder, dst)

                log.info('[updater] exec install.bat')
                os.system(os.sep.join([dst, 'install.bat']))

            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

                '''exception raised, then rollback py-ubx'''
                if svc_mgr.getStatus() is not True:
                    os.system(os.sep.join([dst_bak, 'install.bat']))

        else:
            log.info('py-ubx is latest version: '+local_ver)

    except Exception, e:
        log.error(str(e))


"""export props"""
kiosk_conf = parse_kiosk_conf()
kiosk_id = kiosk_conf['kioskid']
owner_id = kiosk_conf['ownerid']
ubkiosk_dir = kiosk_conf['ubkiosk_dir']

if __name__ == '__main__':
    checking_update()
