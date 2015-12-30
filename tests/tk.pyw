#!/usr/bin/env python
# _*_ coding: utf-8 _*_

__author__ = 'sunnyw'
__doc__= '编写非控制台程序，不需要用到stdin, stdout, stderr， 请将扩展名改为.pyw, 使用pythonw 解释器'

"""use tkinter to build win32 gui app"""
# import Tkinter as tk
from Tkinter import *
"""show test box and tk version"""
# tk._test()
"""setup top window obj"""
root=Tk()
root.title('test pack layout')

"""顶层窗口初始化大小"""
root.geometry('1000x800')

frm=Frame(root, relief=RIDGE, borderwidth=2)
Label(frm, text='unibox sync app').pack()
Button(frm, text='A').pack(side=LEFT, fill=X, padx=10, ipadx=10)
Button(frm, text='B').pack(side=LEFT, fill=X)

frm.pack(fill=X, expand=1)

"""place widget obj"""
# Label(root, text='hello,world', font='consolas').pack()
# btn=Button(root, text='exit', command=root.quit, bg='#e8e8e8', fg='black')
# btn.pack()

"""show a login box"""
# Label(root, text="Username").grid(row=0, sticky='w')
# Label(root, text="Password").grid(row=1, sticky='w')
# Entry(root).grid(row=0, column=1, sticky='e')
# Entry(root).grid(row=1, column=1, sticky='e')
# btn=Button(root, text="Login").grid(row=2, column=1, sticky='e')


root.mainloop()