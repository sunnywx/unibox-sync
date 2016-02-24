#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'common props and methods by unibox apps'

import util
import logger
import os
import sys
import inspect
from zipfile import *
import urllib2
import lib.inet as inet
import shutil
import time
import traceback

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


"""export props"""
kiosk_conf = parse_kiosk_conf()
kiosk_id = kiosk_conf['kioskid']
owner_id = kiosk_conf['ownerid']
ubkiosk_dir = kiosk_conf['ubkiosk_dir']

'''py-ubx destination dir'''
dst='c:\\py-ubx'

dst_deps=os.sep.join([dst, 'deps'])

'''py-ubx backup destination dir'''
dst_bak=dst+'-bak'

'''py-ubx build dependencies'''
build_deps=[
    'psutil-3.3.0.win32-py2.7.exe',
    'pywin32-219.win32-py2.7.exe'
]

upd_svr=kiosk_conf['update_server'].replace('\'', '').strip('\'')     # careful trail slash :(
if upd_svr[-1] != '/':
    upd_svr += '/'

'''-----------------------------------------------------------------+
'''
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

    local_prefix=local_ver.split('-')[0]
    online_prefix=online_ver.split('-')[0]

    if local_prefix == online_prefix:
        local_suffix=local_ver[len(local_prefix)+1:]
        online_suffix=online_ver[len(online_prefix)+1:]

        if local_suffix == '':  # stable version
            return 1
        if online_suffix == '':
            return -1

        return -1 if local_suffix < online_suffix else 1

    return -1 if local_ver < online_ver else 1


def backup_files(from_path, to_path, clean_dst=True):
    import shutil
    if os.path.isdir(to_path):
        if clean_dst is True:
            shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)


def dl_deps():
    '''首次编译，下载python依赖包，以后在租赁机上重编ubx，可以从本地获取
        从 原始py-ubx目录或者tmp目录查找deps包， 查找失败再从网络获取
    '''
    orig_deps=os.sep.join([dst_bak, 'deps'])
    tmp_deps=util.sys_tmp(filename='ubx-deps')

    '''check ubx-deps if empty'''
    deps_len=len(build_deps)
    if os.path.exists(tmp_deps):
        tmp_deps_len = len(os.listdir(tmp_deps))
        if tmp_deps_len==0 or tmp_deps_len < deps_len:
            '''tmp deps dir is not fullly downloaded, remove it'''
            shutil.rmtree(tmp_deps)

    if os.path.exists(orig_deps):
        backup_files(orig_deps, dst_deps)

    elif os.path.exists(tmp_deps):
        backup_files(tmp_deps, dst_deps)

    else:
        '''download deps from net'''
        for f in build_deps:
            inet.download_file(upd_svr + 'ubx-deps/' + f)
            if not os.path.isdir(tmp_deps):
                os.mkdir(tmp_deps)

            tmp_f=util.sys_tmp(filename=f)
            shutil.copy2(tmp_f, os.sep.join([tmp_deps, f]))
            os.unlink(tmp_f)

        backup_files(tmp_deps, dst_deps)

def copy_recursive(src, dst):
    count_copy=0
    for f in os.listdir(src):
        cur=os.sep.join([src, f])
        dst_cur=os.sep.join([dst, f])
        if os.path.isdir(cur):
            copy_recursive(cur, dst_cur)
        else:
            try:
                shutil.copy2(cur, dst_cur)
                count_copy=count_copy+1
            except Exception, e:
                log.error('copy recursve failed: '+str(e))

    return count_copy

def checking_update():
    req_online_ver=upd_svr+'update.txt'
    try:
        resp = urllib2.urlopen(req_online_ver)
        online_ver=resp.read().strip('\n')
        local_ver=get_app_version()

        if compare_version(local_ver, online_ver) < 0:
            # download zip-ball
            zip_file='py-ubx-' + online_ver + '.zip'

            log.info('[updater] download zip: ' + upd_svr + zip_file)
            inet.download_file(upd_svr + zip_file)

            zip_ubx = ZipFile(util.sys_tmp(None, zip_file), 'r')
            extract_folder=util.sys_tmp(filename='ubx-update')

            log.info('[updater] extract '+online_ver+' files to '+extract_folder)
            zip_ubx.extractall(extract_folder)

            # os.system('NET STOP UniboxSvc')
            import svc
            svc_mgr=svc.SvcManager()
            svc_mgr.stop()

            try:
                # import psutil
                # relative_process=['pythonservice.exe', 'net.exe', 'python.exe', 'cmd.exe']
                # plist = {}
                # for p in psutil.process_iter():
                #     plist[p.name()] = p.pid
                #
                # try:
                #     for x in relative_process:
                #         if x in plist.keys():
                #             log.info('[updater] killing process with py-ubx: '+x)
                #             os.system('taskkill /f /im '+x)
                # except Exception, e:
                # #log.error('[updater] kill process failed: '+str(e))

                os.chdir(os.path.dirname(dst))
                cnt_copy_file=copy_recursive(extract_folder, dst)

                log.info('[updater] call post-script: install.bat')
                os.system(os.sep.join([dst, 'install.bat']))      # may raise access denied
                log.info('[updater] py-ubx revision to '+online_ver+', overwrite '+cnt_copy_file+' files')

            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

                '''exception raised, then rollback py-ubx'''
                log.info('[updater] updating failed, rollback')

                # '''保留原始程序的日志和配置'''
                # reserved_file_map={
                #     'apps/Sync/log': 'sync_log',
                #     'apps/Sync/sync_app.ini': 'sync_app.ini',
                #     'apps/Monitor/log': 'monitor_log',
                #     'apps/Monitor/monitor_app.ini': 'monitor_app.ini',
                #     'log': 'ubx_log'
                # }

            # os.system('NET START UniboxSvc')
            svc_mgr.start()

            '''lazy download build deps to optimize perf'''
            if not os.path.exists(dst_deps):
                dl_deps()

        else:
            log.info('py-ubx is latest version: '+local_ver)

    except Exception, e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))


if __name__ == '__main__':
    checking_update()
