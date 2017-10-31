# -*- coding: utf-8 -*-
import json
import re
from urllib import parse as urllib

import datetime
import jsonpath
import scrapy

from weibo.items import KeyItem, MsgItem, CommentItem
import time

class WeibospiderSpider(scrapy.Spider):
    name = 'weibospider'
    allowed_domains = ['weibo.cn']
    # 搜索的关键字
    key_word = '美妆'

    # x = '0'
    # y = '0'
    # z = '0'
    # interval_time = [x, y, z]  # 分\时\天
    # if interval_time[2].isdigit() and interval_time[2] > 0:
    #     interval_time = [0, 0, z]
    # elif interval_time[1].isdigit() and interval_time[1] > 0:
    #     interval_time = [0, y, 0]
    # elif interval_time[0].isdigit() and interval_time[0] >= 0:
    #     interval_time = [x, 0, 0]
    # time_stamp = 10000

    # 查多少页微博
    page_num = 5

    # 定义大V粉丝数下限,默认1000000粉
    fan_limit = 100000
    word_encoded = urllib.urlencode({'key_word': key_word})[9:].replace(r'%', '%25')
    page = 1
    urlstr = 'https://m.weibo.cn/api/container/getIndex?' \
             'containerid=100103type%253D17%2526q%253D' \
             '{0}&page={1}'.format(word_encoded, page)
    user_list = []
    start_urls = [urlstr]

    def parse(self, response):
        json_obj = json.loads(response.text)
        # 找到各节点
        name_list = jsonpath.jsonpath(json_obj, '$..screen_name')
        id_list = jsonpath.jsonpath(json_obj, '$..id')
        fan_num_list = jsonpath.jsonpath(json_obj, '$..followers_count')
        profile_list = jsonpath.jsonpath(json_obj, '$..profile_url')
        # zip处理,转成生成器
        key_list = (i for i in zip(name_list, id_list, fan_num_list, profile_list))
        for name, id_, fan_num, profile in key_list:
            if id_ in self.user_list:
                continue
            else:
                self.user_list.append(id_)
            # 粉丝数包含"万"则转为整数
            if not str(fan_num).isdigit():
                fan_num = int(fan_num[:-1]) * 10000
            # 大于定义的大V粉丝数下限的用户则收录,否则舍弃
            if fan_num > self.fan_limit:
                key = KeyItem()
                print("+", name)
                key['name'] = name
                key['key_id'] = id_
                key['fan_num'] = int(fan_num)
                # 无实际用处
                key['profile_link'] = profile

                yield key
                # 构造用户详情页的微博列表 json请求,用于获取第一页微博的id
                for page in range(1, self.page_num):
                    url = 'https://m.weibo.cn/api/container/getIndex?' \
                          'uid={0}&containerid=107603{1}&page={2}'.format(id_, id_, page)
                    yield scrapy.Request(url, meta={'key_id': id_}, callback=self.parse_msg)
        self.page += 1
        urlstr = 'https://m.weibo.cn/api/container/getIndex?' \
                 'containerid=100103type%253D17%2526q%253D' \
                 '{0}&page={1}'.format(self.word_encoded, self.page)
        # 构造用户列表页 下一页请求
        yield scrapy.Request(urlstr, callback=self.parse)

    # 用户详情页
    def parse_msg(self, response):
        json_obj = json.loads(response.text)
        itemid_list = jsonpath.jsonpath(json_obj, '$..itemid')
        scheme_list = jsonpath.jsonpath(json_obj, '$..scheme')
        time_list = jsonpath.jsonpath(json_obj, '$..created_at')

        for itemid, scheme, pub_time in zip(itemid_list, scheme_list, time_list):
            if re.findall(r'\d+_-_\d+', itemid):
                msg_item = MsgItem()
                msg_item['pub_time'] = pub_time
                # current_date = datetime.date.today()
                # if '小时' in pub_time:
                #     month = pub_time[:2] if pub_time[:2][0]!=0 else pub_time[1]
                #     day = pub_time[3:] if pub_time[3:][0]!=0 else pub_time[4]
                # elif '分钟' in pub_time:
                #     months = current_date.month
                #     days = current_date.day
                #     then_time = datetime.datetime(current_date.year, months, days, hours, mins)
                #     interval_ = time.mktime(current_date.timetuple()) - time.mktime(then_time.timetuple())
                #     if interval_ > self.time_stamp:
                #         break
                # elif '昨天' in pub_time:
                #     months = current_date.month
                #     days = current_date.day
                #     hours = pub_time[3:5] if pub_time[3]!=0 else pub_time[4]
                #     mins = pub_time[6:] if pub_time[6]!=0 else pub_time[7]
                #     then_time = datetime.datetime(current_date.year, months, days, hours, mins)
                #     interval_ = time.mktime(current_date.timetuple()) - time.mktime(then_time.timetuple())
                #     if interval_ > self.time_stamp:
                #         break
                # else:
                #     month = pub_time[:2] if pub_time[:2][0]!=0 else pub_time[1]
                #     day = pub_time[3:] if pub_time[3:][0]!=0 else pub_time[4]
                #     then_time = datetime.datetime(current_date.year,month,day)
                #     interval_ = time.mktime(current_date.timetuple()) - time.mktime(then_time.timetuple())
                #     if interval_ > self.time_stamp:
                #         break
                msg_item['key_id'] = response.meta['key_id']
                msg_item['weibo_link'] = scheme
                # itemid是某条微博的id
                itemid = itemid.split('_-_')
                msg_item['weibo_id'] = itemid
                yield msg_item
                # 处理报错
                try:
                    itemid = itemid[1]
                except:
                    print('错误:' + response.url)
                    print('错误:' + str(itemid))
                else:
                    # 要先发起第一个请求才能获得max值
                    url = 'https://m.weibo.cn/api/comments/show?id={0}&page=1'.format(itemid)
                    # 构造微博详情页的评论列表 json请求 用于获取评论
                    yield scrapy.Request(url, meta={'key_id': response.meta['key_id'], 'itemid': itemid},
                                         callback=self.parse_comment)

    # 用于获取评论
    def parse_comment(self, response):
        json_obj = json.loads(response.text)
        try:
            itemid = response.meta['itemid']
            key_id = response.meta['key_id']
        except:
            print(response.meta)
            raise KeyError
        if response.meta.get('filter_'):
            filter_ = response.meta.get('filter_')
        else:
            # 构建内存去重:过滤器
            filter_ = (i for i in [])

        id_list = jsonpath.jsonpath(json_obj, '$..id')
        # 如果该条微博下存在评论
        if id_list:
            name_list = jsonpath.jsonpath(json_obj, '$..screen_name')
            text_list = jsonpath.jsonpath(json_obj, '$..text')
            time_list = jsonpath.jsonpath(json_obj, '$..created_at')
            for id_, name, text, time_ in zip(id_list, name_list, text_list, time_list):
                if id_ not in filter_:
                    comment_item = CommentItem()
                    comment_item['key_id'] = key_id
                    comment_item['weibo_id'] = itemid
                    comment_item['name'] = name
                    comment_item['pub_text'] = text
                    comment_item['pub_time'] = time_
                    # 将本条采集的评论加入过滤器
                    # print(filter_)
                    l = [i for i in filter_]
                    l.append(id_)
                    filter_ = (j for j in l)
                    yield comment_item

            # 最大评论页数
            max_page = jsonpath.jsonpath(json_obj, '$..max')[0]
            print(max_page)
            if response.meta.get('current_page'):
                # 记录当前的页面
                current_page = response.meta.get('current_page')
            else:
                current_page = 1
            for page_index in range(current_page + 1, max_page + 1):
                comment_url = 'https://m.weibo.cn/api/comments/show?id={0}&page={1}'.format(itemid, page_index)
                yield scrapy.Request(comment_url, meta={'key_id': key_id, 'itemid': itemid, 'current_page': page_index},
                                     callback=self.parse_comment)
