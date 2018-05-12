# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy.pipelines.images import ImagesPipeline
import codecs, json
from scrapy.exporters import JsonItemExporter
import MySQLdb, MySQLdb.cursors
#adbapi 将mysql 异步化
from twisted.enterprise import adbapi


# 数据入库 excute_sort = 300
class BolescrapyPipeline(object):
    def process_item(self, item, spider):
        return item


# 保存json的pipelines
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):

        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    # spider 结束后执行

    def spider_closed(self, spider):
        self.file.close()


# 调用scrapy提供的json export 导出json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

# 继承scrapy的imagespipelines，获取下载到本地的图片的url， excute_sort = 1
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for tof, value in results:
            image_file_path = value["path"]
        item["front_image_path"] = image_file_path
        return item


# 自定义mysql pipeline, 耗时 14分钟
class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect('192.168.0.100', 'root', '123456', 'scrapydb', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            INSERT INTO jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path, \
            comment_num, vote_num, storeup_num, tags, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(insert_sql, (item["title"], item["create_date"], item["url"], item["url_object_id"], item["front_image_url"], item["front_image_path"], item["comment_num"], item["vote_num"], item["storeup_num"], item["tags"], item["content"]))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print e


# scrapy 框架提供的mysql异步插入
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    # 获取setting.py中定义的数据from_settings
    @classmethod
    def from_settings(cls, settings):
        dbparams = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset = 'utf8',
            cursorclass = MySQLdb.cursors.DictCursor,
            use_unicode = True
        )

        # 调用twisted提供的api将mysql异步化
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparams)

        return cls(dbpool)

    # 使用twisted将mysql插入变成异步执行
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 调用异步错误处理
        query.addErrback(self.handle_error)

    # 异步错误处理
    def handle_error(self, failure):
        print failure

    def do_insert(self, cursor, item):
        # 执行具体的插入操作
        insert_sql = """
                    INSERT INTO jobbole_article_twisted(title, create_date, url, url_object_id, front_image_url, front_image_path, \
                    comment_num, vote_num, storeup_num, tags, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
        cursor.execute(insert_sql, (
        item["title"], item["create_date"], item["url"], item["url_object_id"], item["front_image_url"],
        item["front_image_path"], item["comment_num"], item["vote_num"], item["storeup_num"], item["tags"],
        item["content"]))
