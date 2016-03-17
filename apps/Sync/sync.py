#!/usr/bin/env python
# _*_ coding: utf-8 _*_
__author__ = 'wangxi'
__doc__ = 'a unibox sync utility'

import sys
import os
import string
import datetime
import time
import inspect
import json

import lib.logger
import lib.util
import lib.sqlite
import lib.inet
import lib.unibox as unibox

base_dir = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))

logger = lib.logger.Logger('uniboxSync', base_dir).get()


class UniboxSync():
    """配置文件路径"""
    conf_file = base_dir + '/sync_app.ini'

    """sync程序操作的目录"""
    sandbox_dir = 'c:/ubkiosk/'

    """同步配置项"""
    conf = {}

    """请求服务端的url配置"""
    req_urls = {}

    kiosk_id = 0
    owner_id = 0
    server_host = ''

    """是否强制同步"""
    force_sync=False

    """db handler"""
    db=None

    tmp_folder=''

    def __init__(self):
        """parse sync app config"""
        sync_conf = self.get_config()

        if len(sync_conf) == 0:
            logger.error('invalid sync config file')
            sys.exit(-1)

        sync_conf.update(unibox.kiosk_conf)

        self.conf = sync_conf
        self.server_host = self.conf['sync_server']
        self.kiosk_id = self.conf['kioskid']
        self.owner_id = self.conf['ownerid']

        """sync app request uri"""
        self.uri_map = {
            'ad': self.server_host + '?m=Api&c=Sync&a=ad',
            'title': self.server_host + '?m=Api&c=Sync&a=title',
            'movie': self.server_host + '?m=Api&c=Sync&a=movie',
            'inventory': self.server_host + '?m=Api&c=Sync&a=inventory',
            'kiosk_info': self.server_host + '?m=Api&c=Sync&a=kiosk&ownerId='
                          + self.owner_id + '&kioskId=' + self.kiosk_id,
            'slot': self.server_host + '?m=Api&c=Sync&a=slot'
        }

        self.db = lib.sqlite.Db(self.sandbox_dir + self.conf['local_db'])
        self.tmp_folder = self.sandbox_dir + self.conf['local_tmp']


    def get_config(self):
        sync_conf = lib.util.parse_config(self.conf_file)
        if type(sync_conf) is dict:
            return sync_conf
        else:
            return {}

    def get_ini(self, key='last_sync'):
        if key in self.conf:
            return int(self.conf[key])

    def update_ini(self, key='last_sync'):
        """update last sync timestamp"""
        return lib.util.update_config(self.conf_file, {str(key): int(time.time())})

    def set_force_sync(self, is_force=False):
        self.force_sync=is_force

    """同步全部数据"""
    def sync_all(self):
        self.sync_inventory()
        self.sync_movie()
        self.sync_title()
        self.sync_kiosk()
        self.sync_ad()
        self.sync_slot()

    """同步广告"""
    def sync_ad(self):
        req_url=self.uri_map['ad']
        if self.force_sync is True:
            self.db.execute("DELETE FROM ad")

        """when use down-sync, you need attach Max(version_num) of local as http get param"""
        version_num=self.db.get_max_version('ad', seq_field='ad_id')
        req_url=lib.inet.encode_url(req_url, {'version_num': version_num})

        logger.info('begin sync ad from '+req_url)
        sync_start=time.time()
        json_data=lib.inet.fetch_data(req_url)
        if json_data is None or len(json_data)==0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        if type(json_data) is tuple and json_data[0] == '[err]':
            """failed to fetch data"""
            logger.error(str(json_data))
            return

        """local db fields need to save"""
        field = ['ad_id','position_id', 'media_type', 'ad_name', 'ad_link', 'ad_img',
                 'ad_url', 'start_time', 'end_time', 'click_count', 'enabled', 'version_num']

        ad_path = self.sandbox_dir+self.conf['ad_local_folder']
        cdn_base = self.conf['cdn_base']
        cnt_img = len(json_data)
        cnt_ignore = cnt_failed = cnt_downloaded = 0
        data_ad={}
        records_failed=[]

        logger.info('downloading ad images...')
        for r in json_data:
            ad_img = cdn_base + r['ad_img']
            item = {}
            for key in field:
                if key in r:
                    if key == 'ad_id' and r[key] == '':
                        continue
                    else:
                        item[key] = r[key]
                else:
                    item[key] = ''
            data_ad[r['ad_id']] = item

            logger.info('fetching ad image: '+ ad_img)
            fetch_res = lib.inet.download_file(url=ad_img, save_folder=ad_path, tmp_folder=self.tmp_folder)

            if fetch_res[0] != 'file_download_failed':
                if fetch_res[0] == 'file_exists':
                    cnt_ignore += 1
                    logger.info('ad file exists, ignored')
                elif fetch_res[0] == 'file_download_ok':
                    logger.info('downloaded ad image:' + str(fetch_res[1]))
                    cnt_downloaded += 1
            else:
                """file download failed"""
                logger.error('failed to download ad file: '+ ad_img)
                records_failed.append(r['ad_id'])
                cnt_failed += 1
                continue

        field, params = lib.util.unpack_data(data_ad)
        aff_rows=self.db.replace_many('ad', field, params)

        logger.info('end sync ad, updated '+str(aff_rows)+' rows of ad')
        logger.info('downloaded '+str(cnt_downloaded)+', ignored '+ str(cnt_ignore)+' ad')
        self.update_ini()
        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    """同步电影"""
    def sync_movie(self):
        req_url=self.uri_map['movie']
        if self.force_sync is True:
            self.db.execute("DELETE FROM movie")
            """TODO also delete all movie images on local?"""

        version_num=self.db.get_max_version('movie', seq_field='movie_id')
        req_url=lib.inet.encode_url(req_url, {'version_num': version_num})

        logger.info('sync movie from '+req_url)
        sync_start=time.time()
        json_data=lib.inet.fetch_data(req_url)
        if json_data is None or len(json_data)==0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        poster_prefix = self.sandbox_dir + self.conf['movie_local_folder']
        thumb_prefix = self.sandbox_dir + self.conf['moviethumb_local_folder']
        cdn_base = self.conf['cdn_base']

        """download movie poster and thumbnail images"""
        cnt_fetch_img = len(json_data)
        cnt_poster_ignore = cnt_poster_failed = cnt_poster_downloaded = 0
        cnt_thumb_ignore = cnt_thumb_failed = cnt_thumb_downloaded = 0

        """delay update movie poster / thumbnail"""
        """sqlite 不强制约束数据类型，integer可以插入字符串 ?"""
        """movie_name not be null, check the DDL of movie, movie_id unique index,
        when replace into movie, if index is changed will call update else call insert"""

        field = ['movie_id', 'movie_name', 'director', 'actor', 'genre', 'running_time',
                 'nation', 'release_time', 'play_time', 'dub_language', 'subtitling',
                 'audio_format', 'content_class', 'color', 'per_number', 'medium', 'bar_code',
                 'isrc_code', 'area_code', 'import_code', 'fn_name', 'box_office', 'bullet_films',
                 'issuing_company', 'copyright', 'synopsis', 'movie_desc',
                 'movie_img', 'movie_img_url', 'movie_thumb', 'movie_thumb_url', 'version_num',
                 'movie_name_pinyin', 'movie_name_fpinyin']
        data_movie = {}

        """hold all fail-downloaded rows"""
        records_failed = {
            'poster': [],
            'thumb': []
        }

        if type(json_data) is tuple and json_data[0] == '[err]':
            """failed to fetch data"""
            logger.error(str(json_data))
            return

        for r in json_data:
            """first we download movie_poster, then download thumbnail,
            if these two are downloaded, then update this row's field, this will minimal db lock"""
            poster_img = cdn_base + str(r['movie_img'])
            thumb_img = cdn_base + (str(r['movie_thumb']) if r.has_key('movie_thumb') else str(r['movie_img']))
            item = {}
            for key in field:
                if key == 'movie_id' and r[key] == '':
                    continue
                else:
                    if not r.has_key(key):
                        if key in ['movie_img_url', 'movie_thumb', 'movie_thumb_url']:
                            val=r['movie_img']
                        else:
                            val=''
                    else:
                        val=r[key]

                    item[key] = val

            data_movie[r['movie_id']] = item

            """downloading movie poster image"""
            logger.info('fetching movie poster: '+ poster_img )
            fetch_poster = lib.inet.download_file(url=poster_img, save_folder=poster_prefix, tmp_folder=self.tmp_folder)
            if fetch_poster[0] != 'file_download_failed':
                if fetch_poster[0] == 'file_exists':
                    cnt_poster_ignore += 1
                    logger.info('movie poster exists, ignored ')
                elif fetch_poster[0] == 'file_download_ok':
                    logger.info('downloaded movie poster:' + str(fetch_poster[1]))
                    cnt_poster_downloaded += 1
                """fetch_poster[1] as movie_img"""
                data_movie[r['movie_id']]['movie_img'] = fetch_poster[1]
            else:
                """record failed row"""
                logger.error('failed to download poster: '+ poster_img)
                records_failed['poster'].append(r['movie_id'])
                cnt_poster_failed += 1
                continue

            """downloading movie thumbnail image"""
            logger.info('fetching movie thumbnail: '+ thumb_img)
            fetch_thumb = lib.inet.download_file(url=thumb_img, save_folder=thumb_prefix, tmp_folder=self.tmp_folder)
            if fetch_thumb[0] != 'file_download_failed':
                if fetch_thumb[0] == 'file_exists':
                    cnt_thumb_ignore += 1
                    logger.info('movie thumbnail exists, ignored ')
                elif fetch_thumb[0] == 'file_download_ok':
                    logger.info('downloaded movie thumbnail:' + str(fetch_thumb[1]))
                    cnt_thumb_downloaded += 1
                    
                if r['movie_id'] in data_movie:
                    data_movie[r['movie_id']]['movie_thumb'] = fetch_thumb[1]
            else:
                logger.error('failed to download thumbnail: '+ thumb_img)
                records_failed['thumb'].append(r['movie_id'])
                cnt_thumb_failed += 1
                continue

        """write params_movie_img to local db"""
        field, params = lib.util.unpack_data(data_movie)
        aff_rows=self.db.replace_many('movie', field, params)

        logger.info('end sync movie, updated '+str(aff_rows)+' rows of movie')
        logger.info('downloaded '+str(cnt_poster_downloaded)+', ignored '+ str(cnt_poster_ignore)+' movie poster')
        logger.info('downloaded '+str(cnt_thumb_downloaded)+', ignored '+ str(cnt_thumb_ignore)+' movie thumbnail')

        self.update_ini()
        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    """同步title & title_flags"""
    def sync_title(self):
        req_url=self.uri_map['title']
        if self.force_sync is True:
            self.db.execute("DELETE FROM title")
            self.db.execute("DELETE FROM title_flags")

        version_num=self.db.get_max_version('title', seq_field='title_id')
        req_url=lib.inet.encode_url(req_url, {'version_num': version_num})

        logger.info('sync title & title_flags from '+req_url)
        sync_start=time.time()
        json_data=lib.inet.fetch_data(req_url)
        if json_data is None or len(json_data)==0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        if type(json_data) is tuple and json_data[0] == '[err]':
            """failed to fetch data"""
            logger.error(str(json_data))
            return

        """save to db"""
        field_title = ['title_id', 'movie_id', 'game_id', 'shop_price',
                       'market_price', 'daily_fee', 'deposit','stock_number',
                       'rent_time', 'is_delete', 'is_blueray', 'version_num',
                       'contents_type', 'screen_def', 'screen_dim']

        field_flags = ['title_id', 'coming_soon_begin', 'coming_soon_end', 'hot_begin', 'hot_end',
                       'new_release_begin', 'new_release_end', 'available_begin', 'available_end',
                       'search_on_web_begin', 'search_on_web_end', 'browse_on_web_begin', 'browse_on_web_end',
                       'best_begin', 'best_end', 'version_num']
        param_title = []
        param_flags = []
        for r in json_data:
            row_title = []
            row_flags = []
            for key in field_title:
                if key in r:
                    """title_id must be check"""
                    if key == 'title_id' and r[key] == '':
                        continue
                    else:
                        row_title.append(r[key])
                else:
                    row_title.append('')
            param_title.append(tuple(row_title))

            for key in field_flags:
                if key in r:
                    if key == 'title_id' and r[key] == '':
                        continue
                    else:
                        row_flags.append(r[key])
                else:
                    row_flags.append('')
            param_flags.append(tuple(row_flags))

        aff_rows_title = self.db.replace_many('title', field_title, param_title)
        logger.info('end sync title, '+ str(aff_rows_title) + ' rows of title updated')

        aff_rows_flags = self.db.replace_many('title_flags', field_flags, param_flags)
        logger.info('end sync title_flags, '+ str(aff_rows_flags) + ' rows of title_flags updated')

        self.update_ini()
        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    '''同步库存'''
    def sync_inventory(self):
        sync_start=time.time()
        req_url=self.uri_map['inventory']
        """up-sync fetch max-version from server"""
        server_max_version=lib.inet.fetch_data(self.server_host+'?m=Api&c=Sync&a=maxVersion&kioskId=' + self.kiosk_id)
        if type(server_max_version) is dict and server_max_version['max_ver'] is not None:
            server_max_version = int(server_max_version['max_ver'])
        else:
            server_max_version = -1

        logger.info('[inventory]server version_num='+ str(server_max_version))
        logger.info('up sync inventory, req_url: '+req_url+', kioskId='+self.kiosk_id+',ownerId='+self.owner_id)
        """save local db fields"""
        field=['title_id','kiosk_id','slot_id','member_id','owner_id',
                      'disk1_rfid','disc_status_code','create_time','update_time', 'version_num']

        '''if use force_sync, up sync all local inventory, this only for dev/test'''
        if server_max_version == -1 or self.force_sync:
            """post all local inventory because server is the initial state"""
            filter_cond = '1=1'
        else:
            filter_cond = 'version_num>' + str(server_max_version)

        fetch_sql = "select " + ','.join(field) + " from inventory where " + filter_cond
        logger.info('[SQL]' + fetch_sql)

        local_inventory = self.db.get_many(fetch_sql)
        list_inventory = []
        for item in local_inventory:
            dic = {}
            for dx in range(len(item)):
                key = field[dx]
                value = item[dx]
                dic[key] = value
            list_inventory.append(dic)

        if len(list_inventory) == 0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        post_param = {
            "data": json.dumps(list_inventory),
            'kioskId': self.kiosk_id,
            'ownerId': self.owner_id
        }
        resp_body, resp_status = lib.inet.http_post(req_url, self.server_host, post_param)
        resp_body = json.loads(resp_body)

        if resp_status == 'OK':
            """add detailed sync log"""
            resp_data=resp_body['data']
            if len(resp_data) > 0:
                for row in resp_data:
                    logger.info('[' + str(row['type']) + '] row: rfid=' + str(row['rfid'])+\
                          ',disc_status_code='+ str(row['disc_status_code']) )

            logger.info('sync inventory OK, ' + str(resp_body['updated']) + ' inventory affected')
            self.update_ini()
        else:
            logger.error('sync inventory failed, '+str(resp_body)+'')

        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    '''同步插槽'''
    def sync_slot(self):
        sync_start=time.time()
        req_url=self.uri_map['slot']
        """actually slot data should not be deleted from local"""
        # if force_sync is True:
        #     db.execute("DELETE FROM slot")
        version_num=self.db.get_max_version('slot', seq_field='slot_id')
        req_url=lib.inet.encode_url(req_url, {
            'version_num': version_num,
            'kioskId': self.kiosk_id
        })

        logger.info('begin sync slot from ' + req_url)
        field=['kiosk_model', 'slot_id', 'slot_disuse', 'distance', 'version_num']
        json_data=lib.inet.fetch_data(req_url)
        if json_data is None or len(json_data)==0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        if type(json_data) is tuple and json_data[0] == '[err]':
            """failed to fetch data"""
            logger.error(str(json_data))
            return

        data_slot={}
        if type(json_data) is dict:
            json_data=[json_data]
        for r in json_data:
            item = {}
            for key in field:
                if key in r:
                    if key == 'slot_id' and r[key] == '':
                        continue
                    else:
                        item[key] = r[key]
                else:
                    item[key] = ''
            data_slot[r['slot_id']] = item

        field, params = lib.util.unpack_data(data_slot)
        aff_rows = self.db.replace_many('slot', field, params)
        logger.info('' + str(aff_rows) + ' slot updated')
        self.update_ini()
        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

    '''同步租赁机数据'''
    def sync_kiosk(self):
        sync_start=time.time()
        req_url=self.uri_map['kiosk_info']
        if self.force_sync is True:
            self.db.execute("DELETE FROM kiosk")

        version_num=self.db.get_max_version('kiosk', seq_field='kiosk_id')
        req_url=lib.inet.encode_url(req_url, {'version_num': version_num})

        logger.info('sync kiosk info from '+req_url)
        json_data = lib.inet.fetch_data(req_url)
        if json_data is None or len(json_data) == 0:
            self.update_ini()
            logger.info('already updated, end sync')
            return

        if type(json_data) is tuple and json_data[0] == '[err]':
            """failed to fetch data"""
            logger.error(str(json_data))
            return

        """delete kiosk other than this kiosk_id"""
        # del_kiosk=db.execute("DELETE FROM kiosk WHERE kiosk_id != " + items.kiosk_id)
        # logger.info('removed '+str(del_kiosk)+' kiosk which kioskId != ' + items.kiosk_id )

        """begin update kiosk"""
        field = ['kiosk_id', 'owner_id', 'kiosk_name', 'indoor', 'machine_serial', 'kiosk_model',
                 'kiosk_image', 'kiosk_status', 'state_code', 'city_name', 'location', 'reg_date',
                 'close_date', 'remote_service_ip', 'remote_service_port', 'remote_service_password',
                 'remote_ip', 'remote_port', 'remote_password', 'tax_rate', 'address',
                 'zipcode', 'remark', 'latitude', 'longitude', 'version_num']

        data_kiosk={}
        if type(json_data) is dict:
            json_data=[json_data]
        for r in json_data:
            item = {}
            for key in field:
                if key in r:
                    if key == 'kiosk_id' and r[key] == '':
                        continue
                    else:
                        item[key] = r[key]
                else:
                    item[key] = ''
            data_kiosk[r['kiosk_id']] = item

        field, params = lib.util.unpack_data(data_kiosk)
        aff_rows = self.db.replace_many('kiosk', field, params)
        logger.info('end sync kiosk_info, updated ' + str(aff_rows) + ' rows of kiosk')
        self.update_ini()
        sync_end=time.time()
        logger.info('time elapsed '+ str(sync_end-sync_start) + 'sec\n')

if __name__ == '__main__':
    sync_app=UniboxSync()

    try:
        sync_app.sync_all()
    except Exception, err:
        logger.error('[sync_app] raise error: '+str(err))
