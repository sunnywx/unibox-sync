#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'common helpers for unibox apps'

import util
import logger
import os
import sys
import inspect
import zipfile
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
dst=kiosk_conf['ubx_dir']
dst=dst.replace('/', os.sep).rstrip(os.sep)

dst_deps=os.sep.join([dst, 'deps'])

'''py-ubx build dependencies'''
build_deps=[
    # 'psutil-3.3.0.win32-py2.7.exe',
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
    """首次编译，下载python依赖包，以后在租赁机上重编ubx，可以从本地获取
        从 原始py-ubx目录或者tmp目录查找deps包， 查找失败再从网络获取
    """
    # cwd=os.getcwd()
    # install_log=os.popen(os.sep.join([cwd,'install.bat']))
    #
    # try:
    #     log.info(str(install_log.read()))
    # except Exception,e:
    #     log.error(str(e.message))

    # check if pywin32 lib in pip list
    pywin32_installed=False

    try:
        pip_list=os.popen('pip list').read().strip()
        if pip_list.find('pywin32') != -1:
            pywin32_installed=True
    except Exception, e:
        log.error(str(e.message))

    if pywin32_installed is False:
        tmp_deps=util.sys_tmp(tmp_folder='ubx-deps')
        for f in build_deps:
            local_f=os.sep.join([tmp_deps, f])
            remote_f=upd_svr + 'ubx-deps/' + f

            '''if dep file in tmp, move it'''
            # if os.path.exists(util.sys_tmp(filename=f)):
            #     shutil.move(util.sys_tmp(filename=f), tmp_deps+os.sep+f)

            if f in os.listdir(tmp_deps):
                if inet.diff_rsize(local_f, remote_f) is False:
                    log.info(f+' is broken, fetch it again...')
                    os.unlink(local_f)
                    log.info('downloading '+remote_f+', just wait seconds...')
                    inet.download_file(remote_f, tmp_deps)
            else:
                log.info(f+' is missing, download it...')
                inet.download_file(remote_f, tmp_deps)

        backup_files(tmp_deps, dst_deps)

        os.system(os.sep.join([dst_deps, 'pywin32-219.win32-py2.7.exe']))

    else:
        print 'pywin32 is installed'
        return

def copy_recursive(src, dst, count_copy=0, rec_files=[]):
    # count_copy=0
    # rec_files=[]
    for f in os.listdir(src):
        cur=os.sep.join([src, f])
        dst_cur=os.sep.join([dst, f])

        if os.path.isdir(cur):
            if not os.path.exists(dst_cur):
                os.mkdir(dst_cur)
            copy_recursive(cur, dst_cur, count_copy, rec_files)
        else:
            shutil.copy2(cur, dst_cur)
            count_copy=count_copy+1
            rec_files.append(cur)

    return count_copy, rec_files

def is_svc_running():
    import subprocess
    return subprocess.check_output('sc query uniboxSvc').find('RUNNING') != -1

def checking_update():
    req_online_ver=upd_svr+'update.txt'
    try:
        resp = urllib2.urlopen(req_online_ver)
        online_ver=resp.read().strip('\n')
        local_ver=get_app_version()

        if compare_version(local_ver, online_ver) < 0:
            zip_file='py-ubx-' + online_ver + '.zip'
            log.info('[updater] download latest zip: ' + str(upd_svr+zip_file))
            inet.download_file(upd_svr + zip_file)

            zip_ubx = zipfile.ZipFile(util.sys_tmp(None, zip_file), 'r')
            extract_folder=util.sys_tmp(tmp_folder='ubx-update')

            log.info('[updater] extract UBX-'+str(online_ver)+' to: '+str(extract_folder) )
            zip_ubx.extractall(extract_folder)

            # os.system('NET STOP UniboxSvc')
            import svc
            import datetime
            import compression

            svc_mgr=svc.SvcManager()
            svc_mgr.stop()

            old_cwd=os.getcwd()
            os.chdir(os.path.dirname(dst))

            cnt_copy_file=0
            rec_files=[]

            if is_svc_running():
                # stop uniboxSvc failed
                log.error('[updater] stop uniboxSvc failed, checking_update terminated')
                return False

            today = ''.join(str(datetime.date.today()).split('-'))
            backup_ubx_zip=util.sys_tmp(None, 'ubx-'+today+'.zip')

            compression.zipdir(dst, backup_ubx_zip, False)

            try:
                cnt_copy_file, rec_files=copy_recursive(extract_folder, dst, cnt_copy_file, rec_files)

                '''remove original sync_app.ini'''
                sync_app_ini=os.sep.join([dst, 'apps/Sync/sync_app.ini'])
                if os.path.exists(sync_app_ini):
                    log.info('[updater] remove '+str(sync_app_ini))
                    os.unlink(sync_app_ini)

                log.info('[updater] call post-script: install.bat')
                os.system(os.sep.join([dst, 'install.bat']))      # may raise access denied
                log.info('[updater] py-ubx revision to '+ str(online_ver) +', updated ' + str(cnt_copy_file) + ' files')

                for f in rec_files:
                    log.info('[updater] update file: '+str(f))

            except Exception, e:
                log.error(logger.err_traceback())

                '''exception raised, then rollback py-ubx'''
                log.info('[updater] updating failed, rollback')

                '''extract backup_zip to py-ubx dir'''
                os.chdir(dst)
                with zipfile.ZipFile(backup_ubx_zip) as zf:
                    zf.extractall()

            if not is_svc_running():
                svc_mgr.start()

    except Exception, e:
        log.error(logger.err_traceback())


if __name__ == '__main__':
    checking_update()