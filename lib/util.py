#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'wangXi'
__doc__ = "common util for sync app"

import os
import sys
import string
import ConfigParser
import logging
import datetime

import logger
import codecs
import inspect
import time
# import msvcrt
import platform

log = logger.Logger().get()

cwd=os.path.dirname(os.path.dirname(inspect.getfile(inspect.currentframe())))

"""parse config file"""
def parse_config(ini_file, section='SYNC'):
    conf = ConfigParser.ConfigParser()

    if os.path.isfile(ini_file):
        conf.readfp(codecs.open(ini_file, "r", "utf-8-sig"))
    else:
        err_msg = 'file not found: ' + ini_file
        log.error(err_msg)
        # sys.exit(-1)

    """try to get section"""
    try:
        sections = conf.items(section)
        return dict(sections)

    except Exception, e:
        log.error(str(e))
        return -1

def update_config(ini_file, set_item={}, section='SYNC'):
    """避免windows BOM头部 section报错"""
    conf = ConfigParser.ConfigParser()

    if os.path.isfile(ini_file):
        try:
            conf.readfp(codecs.open(ini_file, "r", "utf-8-sig"))

            if conf.has_section(section):
                """update section items"""
                for key in set_item:
                    if conf.has_option(section, key):
                        conf.set(section, key, set_item[key])
            else:
                """copy the sample file as ini file"""
                log.error('section:'+str(section)+'not found, copy '+str(ini_file)+'.sample')

                from shutil import copyfile
                sample_conf=ini_file+'.sample'
                """unlink origin ini"""
                os.remove(ini_file)
                copyfile(sample_conf, ini_file)

            fsize=os.path.getsize(ini_file)

            """use plain file to emulate lock"""
            lock_file=os.sep.join([cwd, 'sync.lock'])

            """check lock file, if create time > 2min,remove it"""
            if os.path.exists(lock_file) and (time.time()-os.path.getctime(lock_file)) > 120:
                os.remove(lock_file)

            if not os.path.exists(lock_file):
                flock = open(lock_file, 'w')

                try:
                    config_file=open(ini_file, 'r+')
                    """on windows, write lock"""
                    # fd=config_file.fileno()
                    # msvcrt.locking(fd, msvcrt.LK_RLCK, fsize)
                    conf.write(config_file)
                    # config_file.flush()

                    # msvcrt.locking(fd, msvcrt.LK_UNLCK, fsize)
                    # config_file.close()

                    """on windows endline with \r\n"""
                    # msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, fsize)

                    """
                    r'\n' raw string
                    rewind file pointer
                    """
                    config_file.seek(0)
                    conf_data=config_file.read()

                    if len(conf_data) > 0:
                        config_file.seek(0)
                        data=conf_data.replace(r'\n', r'\r\n').rstrip(os.linesep)
                        config_file.write(data)

                        config_file.flush()
                        os.fsync(config_file.fileno())

                    # msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, fsize)
                    config_file.close()

                except Exception, e:
                    log.error(str(e))

                flock.close()
                os.remove(lock_file)
                return True

            else:
                log.info('lock file:'+lock_file+' exists, ini locked')
                return False

        except Exception, e:
            log.error(str(e))
            return -1

    else:
        log.error('file not found: ' + ini_file)
        return -1

"""simple parse filename from url"""
def parse_filename(url):
    parts = string.split(url, '/')
    raw_name = parts.pop()
    pos = string.find(raw_name, '?')
    if pos > 0:
        """truncate string"""
        raw_name = raw_name[0:pos]

    return raw_name


"""filter input variable"""
def filter_input(val):
    if type(val) is str:
        if val == '' or val == 'NaN':
            return ''
    if type(val) is unicode:
        if val == unicode('') or val == unicode('NaN'):
            return unicode('')

    """if val is dict/list use recursive"""
    if type(val) is dict:
        for key in val:
            val[key] = filter_input(val[key])

    if type(val) is list:
        for i in range(len(val)):
            val[i] = filter_input(val[i])

    return val

"""unpack down-sync fetched data, translate field and params"""
def unpack_data(data={}):
    field = []
    params = []
    if len(data) > 0:
        """just use dict shallow copy"""
        data_copy=data.copy()
        first_item=data_copy.popitem()
        field = first_item[1].keys()
        del data_copy

        for k in data:
            cur=data[k]
            cur_list=[]
            for dx in range(len(field)):
                key_name = field[dx]
                cur_list.append(cur[key_name])
            params.append( tuple(cur_list) )

    return field, params

# set system tmp dolder
def sys_tmp(tmp_folder=None, filename=''):
    if platform.system() == 'Linux':
        tmp_base = '/tmp'
    elif platform.system() == 'Windows':
        # import tempfile
        # print tempfile.mkdtemp()
        tmp_base = 'c:\\Temp'

    if not tmp_folder:
        tmp_folder=tmp_base
    else:
        tmp_folder=os.sep.join([tmp_base, str(tmp_folder)])

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    if filename != '':
        return tmp_folder+os.sep+filename
    else:
        return tmp_folder
