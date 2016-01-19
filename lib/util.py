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
# import msvcrt

log = logger.Logger().get()

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
            lock_file=os.sep.join([os.getcwd(), 'sync.lock'])

            if not os.path.exists(lock_file):
                try:
                    flock=open(lock_file, 'w')

                    config_file=open(ini_file, 'w+')
                    """on windows, write lock"""
                    # fd=config_file.fileno()
                    # msvcrt.locking(fd, msvcrt.LK_RLCK, fsize)
                    conf.write(config_file)
                    # msvcrt.locking(fd, msvcrt.LK_UNLCK, fsize)
                    config_file.close()

                    """on windows endline with \r\n"""
                    f = open(ini_file, 'r+')
                    # msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, fsize)
                    """r'\n' raw string"""
                    conf_data=f.read()
                    if len(conf_data) > 0:
                        conf_data=conf_data.replace(r'\n', r'\r\n')
                        f.seek(0)
                        f.write(conf_data)

                    # msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, fsize)
                    f.close()

                    flock.close()
                    os.remove(lock_file)

                    return True

                except Exception, e:
                    log.error(str(e))

            else:
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
