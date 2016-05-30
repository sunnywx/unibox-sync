#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'wangXi'

import os
import httplib
import urllib
import urllib2
import json
import platform

import lib.util as util

import sys
import time
import tempfile


"""check if sync web server is available"""
def check_server_status(host='api.dev.unibox.com.cn', port=80, timeout=3):
    conn = httplib.HTTPConnection(host, port, timeout)
    conn.request('GET', '/')
    resp = conn.getresponse()

    """return response.body status_code status_text"""
    body, status_code, status_text = resp.read(), resp.status, resp.reason
    conn.close()
    """accept 30x redirect"""
    if 200 <= status_code < 400:
        return True
    else:
        return False

"""检查网络连接，重试三次，每次延时1500ms"""
def check_connection(host='api.dev.unibox.com.cn'):
    ping_st = os.system('ping -n 3 -w 1500 ' + str(host))
    return ping_st == 0


def encode_url(url, data):
    data = urllib.urlencode(data)
    """if data is not None, urlopen will be post request"""
    if url.find('?') != -1:
        url = url + '&' + data
    else:
        url = url + '?' + data
    return url


"""http get client"""
def http_get(url, data=None, timeout=15):
    """timeout 5sec"""
    if data != None:
        url = encode_url(url)

    try:
        response = urllib2.urlopen(url, None, timeout)
        """response encode with json"""
        # resp=response.read()
        resp = json.load(response)
        return resp

    except Exception, e:
        util.log.error(e.message)

        return {
            'status': u'0',
            'data': [],
            'msg': 'http req failed'
        }


def http_post(url, host='', param={}, timeout=5):
    param = urllib.urlencode(param)
    header = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain,text/html,application/json",
        "Connection" :"Keep-Alive"
    }
    host = host.replace('http://', '').rstrip('/')
    try:
        conn = httplib.HTTPConnection(host, timeout=timeout)
        conn.request('POST', url, param, header)
        resp = conn.getresponse()

        body, status_code, status_text = resp.read(), resp.status, resp.reason
        # conn.close()
    except Exception, e:
        util.log.error(str(e))
        body, status_text = [], 'post failed'

    return body, status_text

"""模拟下载进度条"""
def dl_hook(a,b,c):
    ''''
    a:已经下载的数据块
    b:数据块的大小
    c:远程文件的大小
   '''
    remote_fsize=c/1024
    per = 100.0 * a * b / c
    if per > 100:
        per = 100
    x=int(per/2)

    sys.stdout.write("[remote file=%.2fKB],  downloading: [%s%s] %i%%\r" %
                     (remote_fsize,  '#' * x , '-' * (50 - x) , x * 2))
    sys.stdout.flush()
    time.sleep(0.5)

def diff_rsize(fpath, remote_path):
    """get remote file size to check if the original data"""
    print('diff remote file:'+remote_path+' with local:'+fpath)
    try:
        req = urllib2.urlopen(remote_path, timeout=3)
        rsize = req.info().getheaders('Content-Length')[0]

        """get local file size"""
        lsize = os.path.getsize(fpath)
        if int(rsize) == int(lsize):
            return True

    except Exception, e:
        util.log.error(str(e.message))
        return False

"""download remote file"""
def download_file(url, save_folder='', tmp_folder=None):
    """先将文件下载到tmp目录,避免多个进程同时操作该文件"""
    if tmp_folder is None or tmp_folder == '':
        if platform.system() == 'Linux':
            tmp_folder = '/tmp'
        elif platform.system() == 'Windows':
            tmp_folder = 'c:\\Temp'

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    if save_folder == '':
        save_folder=tmp_folder
    else:
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)

    filename = util.parse_filename(url)
    filepath = os.path.join(save_folder, filename)

    if os.path.isfile(filepath):
        if diff_rsize(filepath, url) is False:
            """delete tmp downloaded file"""
            print('local file '+filepath+' not fully downloaded, remove it')
            os.remove(filepath)
        else:
            return 'file_exists', filepath

    if filename == unicode('NaN') or filename == unicode(''):
        return 'file_download_failed', ''

    try:
        """use reporthook to mimic progress bar"""
        tmpfile=os.path.join(tmp_folder, filename)
        fullname, resp_header = urllib.urlretrieve(url, tmpfile, reporthook=dl_hook)

        if resp_header.get('content-length') > 0:
            """move tmpfile to dest dir"""
            os.rename(tmpfile, filepath)
            return 'file_download_ok', filepath
        else:
            return 'file_download_failed', ''

    except Exception, e:
        util.log.error(e.message)
        return 'file_download_failed', ''


def fetch_data(req_url, data=None):
    data = http_get(req_url, data)

    if 'code' in data and data['code'] == unicode(-1):
        util.log.error('bad request uri, sync canceled')
        return '[err]', "bad request uri"
    elif data['status'] != 1:
        util.log.error('fail to download data, sync canceled')
        return '[err]', 'fail to fetch data'
    else:
        return util.filter_input(data['data'])
