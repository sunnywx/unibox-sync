#!/usr/bin/env python
# _*_ coding: gb2312 _*_
__author__ = 'wangxi'
__doc__ = 'Unibox Service as daemon process'

import sys
import os
import getopt

"""need pre-install pywin32"""
import time

import lib.logger
import lib.inet

log =lib.logger.Logger().get()


def usage():
    print """\
    UniBox Service Controller <wangxi@unibox.com.cn>
    Usage: ubsc <-opt|--option> [cmd]
        <-c|--control>
            -c install      将UniboxSvc安装到windows服务
            -c auto         将UniboxSvc安装到服务并随系统自启动
            -c start        启动UniboxSvc服务
            -c stop         停止UniboxSvc服务
            -c status       检查UniboxSvc服务状态
            -c remove       卸载UniboxSvc服务
            -c reload       重启UniboxSvc服务
        <-s|--sync>
            -s all          同步全部数据项
            -s ad           同步ad
            -s title        同步title
            -s movie        同步movie
            -s kiosk        同步kiosk
            -s slot         同步slot
            -s inv          同步库存
            -f|--force      强制同步 (仅用于向下同步和开发测试阶段)
            -s log          查看同步日志
            -s edit         修改同步配置
        <-m|--monitor>
            -m stat         汇总监控数据
            -m plist        本机进程列表
            -m cpu          CPU使用率
            -m mem          内存使用率
            -m disk         硬盘使用率
            -m net          网络IO
            -m log          查看监控日志
            -m edit         修改监控配置

        <-l|--log>          查看UniboxSvc日志
        <-e|--edit>         修改UniboxSvc配置
        <-h|--help>         列出帮助命令
        <-v|--version>      查看程序版本"""


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

    try:
        opt, args = getopt.getopt(args, "hc:s:m:vle",
                                  ["help", "control=",
                                   "sync=", "monitor=", "version", "log", "edit"])
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
                    cur_dir=get_cwd()
                    call_sync = subprocess.check_output('python ' + cur_dir + 'lib/svc.py ' + arg)
                    log.info(call_sync)
                except Exception, e:
                    log.error(e.message)

            elif arg in ['start', 'stop', 'status', 'reload']:
                import lib.svc as svc
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
                print 'ubsc -c|--control [install|auto|remove|start|reload|stop|status]'
                sys.exit(1)

        elif cmd in ['-s', '--sync']:
            import apps.Sync.sync as mod_sync

            ub_sync=mod_sync.UniboxSync()
            ub_sync.set_force_sync(is_force=use_force)

            if arg=='log':
                today_log=get_logfile()
                log_file = mod_sync.base_dir + '/log/' + today_log
                os.system('notepad ' + log_file)
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

                print('===>check network connection...')
                if lib.inet.check_connection(sync_host) is False:
                    log.error('network connection error')
                    return
                print('===>connection ok')
                log.info('===>begin sync ' + str(arg) + ' items...')
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
                    log.info('===>end sync ' + str(arg) + ' items, time elapsed ' + str(sync_ed - sync_st) + 'sec')

                except Exception, e:
                    log.error('===>sync ' + str(arg) + ' items failed, ' + str(e))



        elif cmd in ['-m', '--monitor']:
            # import apps.Monitor as Monitor
            pass

        else:
            if cmd in ('-v', '--version'):
                """just a joke"""
                print 'UniBox sync v1.0.build20151228'
                sys.exit(0)
            elif cmd in ('-h', '--help'):
                usage()
                sys.exit(0)
            elif cmd in ('-l', '--log'):
                log_file = get_cwd() + 'log/' + get_logfile()
                os.system('notepad ' + log_file)
            elif cmd in ('-e', '--edit'):
                conf_file = get_cwd()+'unibox.ini'
                os.system('notepad ' + conf_file)
                sys.exit(0)

if __name__ == '__main__':
    main()