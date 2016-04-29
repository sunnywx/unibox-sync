#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'wangXi'

import string
import sqlite3
import time

from lib import util

"""
simple sqlite wrapper
"""
class Db():
    """static member"""
    db_file=''
    """connection handler"""
    conn = None
    """cursor handler"""
    c = None

    def __init__(self, db_file=''):
        Db.db_file=db_file
        # if Db.conn is None:
        #     self.conn = Db.connect()
        # self.c = self.conn.cursor()

    @staticmethod
    def connect():
        """not use exclusive lock mode, because rental applic's sqlite connection will halt"""
        """the rental application's default timeout is 15 sec"""
        """isolation_level DEFERRED, IMMEDIATE, EXCLUSIVE"""
        Db.conn = sqlite3.connect(Db.db_file, timeout=15)
        Db.c = Db.conn.cursor()

        # Db.conn.isolation_level='IMMEDIATE'
        # Db.conn.execute('BEGIN')
        return Db.conn

    """fetch one row"""
    def get_one(self, sql, param=()):
        Db.connect()
        self.c.execute(sql, param)
        row = self.c.fetchone()
        Db.close()
        return row

    """fetch many rows"""
    def get_many(self, sql, param=()):
        Db.connect()
        self.c.execute(sql, param)
        rows = self.c.fetchall()
        Db.close()
        return rows

    def execute(self, sql):
        Db.connect()
        self.c.execute(sql)
        row_count=self.c.rowcount
        self.conn.commit()
        Db.close()
        """return affected rows"""
        return row_count

    """process many rows, include insert and replace, use tuple as params"""

    def process_many(self, tb_name, op='insert', field=[], param=[]):
        len_field = 0
        if type(field) is list:
            len_field = len(field)
            field = string.join(field, ',')
        elif type(field) is str:
            len_field = len(string.split(field, ','))

        if len(param) > 0:
            for i in range(len(param)):
                """convert to tuple"""
                param[i] = tuple(param[i])

        if field=='' and len(param)==0:
            return 0

        sql_prefix = ''
        if op == 'insert':
            sql_prefix += 'insert into '
        elif op == 'replace':
            sql_prefix += 'replace into '
        else:
            util.log.error('unknown op:' + op, 'err')

        sql_prefix += tb_name + '(' + field + ') values (' \
                      + string.join(['?'] * len_field, ',') + ') '

        param = util.filter_input(param)

        Db.connect()
        self.c.executemany(sql_prefix, param)
        row_count=self.c.rowcount
        """if you just close db connection without call commit() first, your changes will be lost"""
        self.conn.commit()

        Db.close()

        # time.sleep(10)
        return row_count

        # self.conn.commit()
        # self.c.close()

    def insert_many(self, tb, field=[], param=[]):
        return self.process_many(tb, 'insert', field, param)

    """replace into clause"""

    def replace_many(self, tb, field=[], param=[]):
        return self.process_many(tb, 'replace', field, param)

    @staticmethod
    def close():
        Db.conn.close()

    """compare table's sequential field with version_num and fetch the max of both"""
    def get_max_version(self, tb_name, seq_field):
        sql = 'select max(max(version_num), max(' + seq_field + ')) from ' + tb_name
        res = self.get_one(sql)
        if len(res) > 0:
            """when table is empty, res=(None,)"""
            if res[0] is None:
                """when max_version=-1, need to fetch all records"""
                return -1
            elif res[0] == '':
                """when max func failed, res[0]=='' """
                return 0
            else:
                return int(res[0])

        return 0

    """
    PRAGMA table_info([table_name])
    cid  name  type  notnull dflt_value  pk
    return name=> type
    """
    def inspect_tb(self, tb_name):
        q="PRAGMA table_info("+tb_name.strip()+")"
        res=self.get_many(q)
        struc={}
        if type(res) is list and len(res)>0:
            for row in res:
                struc[row[1]]=row[2]

        return struc