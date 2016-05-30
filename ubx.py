#!/usr/bin/env python
# _*_ coding: gb2312 _*_
__author__ = 'wangxi'
__doc__ = 'Unibox Service, unibox X controller'

import sys
import os
import getopt

"""need pre-install pywin32"""
import time

import lib.logger
import lib.inet
import lib.util
import traceback
import string

import lib.unibox

log = lib.logger.Logger().get()


def usage():
    print """\
py-ubx (Author:Wang Xi, unibox sync and monitor cli tool)
Usage: ubx [-opt|--option] cmd
    install             安装ubx
    auto                安装ubx自启动
    start               启动ubx
    stop                停止ubx
    status              检查ubx状态
    remove              卸载ubx
    reload              重启ubx
    -l|--log            ubx日志
    -e|--edit           ubx配置
    -h|--help           ubx使用帮助
    -v|--version        ubx版本号
    ---------------------------------------+
    -s|--sync
        -s all          同步所有项
        -s ad
        -s title
        -s movie
        -s kiosk
        -s slot
        -s inv
        -f|--force      强制同步
        -s log          sync日志
        -s edit         sync配置
    ---------------------------------------+
    -m|--monitor
        -m run          模拟请求
        -m stat         单次监控
        -m cpu          CPU使用率
        -m mem          内存使用率
        -m disk         硬盘使用率
        -m net          网卡流量
        -m log          monitor日志
        -m edit         monitor配置
"""

def get_logfile():
    import datetime
    today_log = ''.join(str(datetime.date.today()).split('-')) + '.log'
    return today_log

def get_cwd():
    import inspect
    cur_dir=os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
    if 'dist' in cur_dir:
        cur_dir=cur_dir.replace('dist', '')
    if cur_dir[len(cur_dir)-1] != '/':
        cur_dir += '/'
    return cur_dir

"""
local database migration
"""
def db_migration():
    cwd=get_cwd()
    mig_dir=cwd.replace('/', os.sep).rstrip(os.sep)+'/migration'
    app_ver=lib.unibox.get_app_version()
    # app_ver='v1.2.6-a'
    seed_f='mig_'+app_ver+'.sql'
    mig_file=os.sep.join([mig_dir, seed_f])

    def strip_mig_file():
        '''remove additional mig file'''
        for f in os.listdir(mig_dir):
            if f not in ['.gitkeep', seed_f]:
                os.unlink(os.path.join(mig_dir, f))

    if os.path.exists(mig_file):
        f=open(mig_file, 'rt')
        mig_sql=string.join([line for line in f.read().strip().split('\n') if line.strip() != ''], os.linesep)
        # tb_target=''
        # tb_target_struct=sync_app.db.inspect_tb(tb_target)
        log.info('[migration] begin migration based on '+mig_file)
        try:
            import apps.Sync.sync as sync
            sync_app=sync.UniboxSync()
            db=sync_app.db
            db.connect()
            cur=db.c
            cur.executescript(mig_sql)
            """output sql each row"""
            for s in mig_sql.split(os.linesep):
                log.info('[migration] '+s)

            log.info('[migration] database migration done')
            db.close()

            # callback sync all items
            import apps.Sync.sync as mod_sync
            ub_sync=mod_sync.UniboxSync()
            ub_sync.sync_all()

        except Exception, e:
            if e.message.find('duplicate column') != -1:
                log.info('[migration]'+str(e.message))
            else:
                log.error('[migration] raise error: '+lib.logger.err_traceback())
        finally:
            strip_mig_file()

    else:
        log.info('[migration] no migration file found')


def main():
    """sys.argv[0] is current script file"""
    args = sys.argv[1:]
    if len(args) == 0:
        usage()
        sys.exit(0)

    """check force tag"""
    use_force=False
    if '-f' in args:
        use_force=True
        args.remove('-f')
    if '--force' in args:
        use_force=True
        args.remove('--force')

    """simplify cmd"""
    ctl_cmd = ['install', 'auto', 'start', 'stop', 'status', 'remove', 'reload']
    if len(args) == 1 and args[0] in ctl_cmd:
        b = args.pop()
        args = ['-c', b]

    try:
        opt, args = getopt.getopt(args, "hc:s:m:vleu:",
                                  ["help", "control=",
                                   "sync=", "monitor=", "version", "log", "edit", "util="])
    except getopt.GetoptError, err:
        log.error(err)
        sys.exit(-1)

    for cmd, arg in opt:
        """sync service manager, delegation"""
        if cmd in ('-c', '--control'):
            if arg in ['auto', 'install', 'remove']:
                if arg == 'auto':
                    sys.argv = sys.argv[:1]
                    arg = '--startup auto install'
                import subprocess
                import inspect
                try:
                    '''use python service'''
                    cur_dir=get_cwd()
                    call_sync = subprocess.check_output('python ' + cur_dir + 'svc.py ' + arg)
                    log.info('[ubx]'+str(call_sync))
                except Exception, e:
                    log.error('[ubx]'+lib.logger.err_traceback())

            elif arg in ['start', 'stop', 'status', 'reload']:
                import svc
                _svc = svc.SvcManager()
                if arg == 'status':
                    _svc.getStatus()
                elif arg == 'start':
                    _svc.start()
                elif arg == 'stop':
                    _svc.stop()
                elif arg == 'reload':
                    _svc.restart()
            else:
                print 'ubx install|auto|remove|start|reload|stop|status'
                sys.exit(1)

        elif cmd in ['-u', '--util']:
            if arg=='dl_deps':
                lib.unibox.dl_deps()

            if arg=='db_mig':
                db_migration()

        elif cmd in ['-s', '--sync']:
            import apps.Sync.sync as mod_sync

            ub_sync=mod_sync.UniboxSync()
            ub_sync.set_force_sync(is_force=use_force)

            if arg=='log':
                today_log=get_logfile()
                log_file = mod_sync.base_dir + '/log/' + today_log
                os.system('notepad ' + log_file)
                sys.exit(0)
            elif arg=='edit':
                conf_file = ub_sync.conf_file
                os.system('notepad ' + conf_file)
                sys.exit(0)
            else:
                sync_host = ub_sync.conf['sync_server']
                """filter server hostname"""
                if sync_host[len(sync_host) - 1] == '/':
                    sync_host = sync_host[:-1]
                if 'http://' in sync_host:
                    sync_host = sync_host.replace('http://', '')

                print('[ubx]check network connection...')
                if lib.inet.check_connection(sync_host) is False:
                    log.error('network connection error')
                    return

                print('[ubx]connection seems good')
                log.info('[ubx]begin sync ' + str(arg) + ' items')
                try:
                    sync_st = time.time()
                    if arg == 'all':
                        ub_sync.sync_all()
                    elif arg == 'ad':
                        ub_sync.sync_ad()
                    elif arg == 'title':
                        ub_sync.sync_title()
                    elif arg == 'movie':
                        ub_sync.sync_movie()
                    elif arg == 'inv':
                        ub_sync.sync_inventory()
                    elif arg == 'kiosk':
                        ub_sync.sync_kiosk()
                    elif arg == 'slot':
                        ub_sync.sync_slot()

                    sync_ed = time.time()
                    log.info('[ubx]end sync ' + str(arg) + ' items, time elapsed ' + str(sync_ed - sync_st) + 'sec')

                except Exception, e:
                    log.error('[ubx]sync ' + str(arg) + ' items failed, ' + lib.logger.err_traceback())

        elif cmd in ['-m', '--monitor']:
            import apps.Monitor.monitor as mod_monitor
            ub_mon = mod_monitor.UniboxMonitor()

            if arg == 'run':
                cnt_send=0
                print '[ubx]testing monitor function every 5 sec\n'
                while True:
                    if cnt_send>=4:
                        print 'testing reached 4 times, exit'
                        break

                    ub_mon.run()
                    cnt_send += 1
                    time.sleep(ub_mon.monitor_interval)

            elif arg == 'stat':
                ub_mon.stat()
            elif arg == 'cpu':
                ub_mon.show_cpu()
            elif arg == 'mem':
                ub_mon.show_mem()
            elif arg == 'disk':
                ub_mon.show_disk()
            elif arg == 'net':
                ub_mon.show_net()
            elif arg == 'log':
                today_log = get_logfile()
                log_file = mod_monitor.base_dir + '/log/' + today_log
                os.system('notepad ' + log_file)
            elif arg == 'edit':
                conf_file = ub_mon.conf_file
                os.system('notepad ' + conf_file)
            sys.exit(0)

        else:
            if cmd in ('-v', '--version'):
                print lib.unibox.get_app_version()
                sys.exit(0)
            elif cmd in ('-h', '--help'):
                usage()
                sys.exit(0)

            elif cmd in ('-l', '--log'):
                log_file = get_cwd() + 'log/' + get_logfile()
                os.system('notepad ' + log_file)
                sys.exit(0)

            elif cmd in ('-e', '--edit'):
                conf_file = get_cwd()+'unibox.ini'
                os.system('notepad ' + conf_file)
                sys.exit(0)

if __name__ == '__main__':
    main()