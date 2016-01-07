#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = ''


import multiprocessing
from multiprocessing import Process
from multiprocessing import Pool
import os
import sys
import time
import logging

def daemon():
    p=multiprocessing.current_process()
    print 'starting:', p.name, p.pid
    sys.stdout.flush()
    '''do something'''
    time.sleep(2)
    print 'exiting:', p.name, p.pid
    sys.stdout.flush()

def non_daemon():
    p=multiprocessing.current_process()
    print 'starting:', p.name, p.pid
    sys.stdout.flush()
    '''do something'''
    time.sleep(2)
    print 'exiting:', p.name, p.pid
    sys.stdout.flush()

def worker():
    p=multiprocessing.current_process()
    print 'starting:', p.name

if __name__=='__main__':
    # multiprocessing.log_to_stderr(logging.DEBUG)
    # p=multiprocessing.Process(target=worker)
    # p.start()
    # p.join()


    d=Process(name='daemon', target=daemon)
    d.daemon=True

    n=Process(name='non_daemon', target=non_daemon)
    n.daemon=False

    d.start()
    time.sleep(2)
    n.start()


