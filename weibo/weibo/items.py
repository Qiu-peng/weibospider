# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

# 大V
class KeyItem(scrapy.Item):
    name = scrapy.Field()
    key_id = scrapy.Field()
    fan_num = scrapy.Field()
    # 仅作收录
    profile_link = scrapy.Field()

# 微博
class MsgItem(scrapy.Item):
    key_id = scrapy.Field()
    weibo_id = scrapy.Field()
    pub_time = scrapy.Field()
    weibo_link = scrapy.Field()

# 评论
class CommentItem(scrapy.Item):
    key_id = scrapy.Field()
    weibo_id = scrapy.Field()
    name = scrapy.Field()
    pub_text = scrapy.Field()
    pub_time = scrapy.Field()