# -*- coding: utf-8 -*-

from weibo.items import *

class KeyJsonPipeline(object):
    def open_spider(self, spider):
        self.kf = open('keys.json','w')
    def process_item(self, item, spider):
        if isinstance(item, KeyItem):
            print(item["name"])
            self.kf.write(str(item)+'\n')
            # print('********')
        return item
    def close_spider(self, spider):
        self.kf.close()

class MsgJsonPipeline(object):
    def open_spider(self, spider):
        self.mf = open('msgs.json','w')
    def process_item(self, item, spider):
        if isinstance(item, MsgItem):
            self.mf.write(str(item)+'\n')
            # print('++++++++')
        return item
    def close_spider(self, spider):
        self.mf.close()

class CommentJsonPipeline(object):
    def open_spider(self, spider):
        self.cf = open('comments.json','w')
    def process_item(self, item, spider):
        if isinstance(item, CommentItem):
            self.cf.write(str(item)+'\n')
            # print('========')
        return item
    def close_spider(self, spider):
        self.cf.close()