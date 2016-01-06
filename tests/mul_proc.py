#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = ''

import multiprocessing
import time
import os

def show_time(label):
    print str(label) + ': ' + time.ctime()

def worker_1(interval):
    show_time('worker_1 start')
    time.sleep(interval)
    show_time('worker_1 end')

def worker_2(interval):
    show_time('worker_2 start')
    time.sleep(interval)
    show_time('worker_2 end')

if __name__ == "__main__":
    print "===>The number of CPU is:" + str(multiprocessing.cpu_count())

    """进程池"""
    proc_pool=[]

    fn_list={'sync':(worker_1, 10), 'monitor':(worker_2, 5)}

    p1 = multiprocessing.Process(name='sync', target = fn_list['sync'][0], args = (fn_list['sync'][1],))
    proc_pool.append(p1)

    p2 = multiprocessing.Process(name='monitor', target = fn_list['monitor'][0], args = (fn_list['monitor'][1],))
    proc_pool.append(p2)

    while True:
        print 'begin loop cycle ', time.ctime()

        for p in proc_pool:
            if p._popen is None:
                p.start()

            if p.is_alive() is False:
                '''进程执行完，已停止'''
                p.terminate()
                p.join()

                '''从进程池移除已停止的进程，重新创建该进程实例'''
                fn=p.name
                proc_pool.remove(p)
                new_proc=multiprocessing.Process(name=fn, target=fn_list[fn][0], args=(fn_list[fn][1],))
                proc_pool.append(new_proc)
                new_proc.start()


        # for p in multiprocessing.active_children():
        for p in proc_pool:
            print("child   p.name:" + p.name + "\tp.pid:" + str(p.pid) + '\tis_alive:'+ str(p.is_alive()) )

        # p1.join()
        # p2.join()

        time.sleep(5)
        # print 'end loop cycle '+ time.ctime()


