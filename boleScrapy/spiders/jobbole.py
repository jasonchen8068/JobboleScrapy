# -*- coding: utf-8 -*-
__author__ = 'jasonchen'
__version__ = '0.0.1'

from scrapy import Spider
import re
from scrapy.http import Request
import urlparse
import datetime

from boleScrapy.items import JobboleArticleItem
from boleScrapy.utils.common import get_md5


class jobboleSpider(Spider):
    # spider name
    name = "jobbole"
    # 爬取域名
    allowed_domains = ["blog.jobbole.com"]
    # 初始列表页url
    start_urls = ["http://blog.jobbole.com/all-posts/"]

    def parse(self, response):
        """
        	1. 获取当前文章列表页中的文章url并交给scrapy
        	2. 获取下一列表页的文章交给scrapy下载，解析
        """
        # 解析列表页中的所有文章的url, post_nodes: 包含url imge
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            # yield 将请求交给scrapy下载分析, extract_first("")：解析成list，获取第一个，默认为空
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            # meta 将数据传送到response
            yield Request(url=urlparse.urljoin(response.url, post_url), meta={'front_image_url': urlparse.urljoin(response.url, image_url)}, callback=self.parse_detail)

        # 提取下一个列表页url
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            # urljoin(a, b) 如果b有域名，则不使用a的域名，如果b没有域名，则使用a提取出来的域名
            yield Request(url=urlparse.urljoin(response.url, next_url), callback=self.parse)

    # 文章详情页爬取
    def parse_detail(self, response):

        # 实例化item
        article_item = JobboleArticleItem()

        # 接收request中传递的meta值
        front_img_url = response.meta.get("front_image_url", "") # 封面图
        title = response.xpath("//div[@class='entry-header']/h1/text()").extract()[0]
        print '标题：', title
        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace(
            u"·", "").strip()
        print '创建时间：', create_date
        vote_num = response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract()[0]
        print '点赞数：', vote_num
        storeup_num = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0]
        storeup_re = re.findall(re.compile(r".*?(\d+).*"), storeup_num.encode('utf8'))
        # print storeup_re
        if storeup_re:
            storeup_num = int(storeup_re[0])
        else:
            storeup_num = 0
        print '收藏数：', storeup_num
        comment_num = response.xpath("//span[contains(@class, 'hide-on-480')]/text()").extract()[0]
        comment_re = re.findall(re.compile(r".*?(\d+).*"), comment_num.encode('utf8'))
        if comment_re:
            comment_num = int(comment_re[0])
        else:
            comment_num = 0
        print '评论数：', comment_num
        # 此处只是将正文的html抓取下来，未做详细处理
        content = response.xpath("//div[@class='entry']").extract()[0]
        # print content
        tags_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tags_list = [elem for elem in tags_list if not elem.strip().endswith(u'评论')]
        tags_str = ','.join(tags_list)
        print '标签：', tags_str

        # 完成爬取，item传值
        article_item["title"] = title
        article_item["url"] = response.url
        article_item["url_object_id"] = get_md5(response.url)
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()

        article_item["create_date"] = create_date
        # scrapy 自带 img pipeline 需要传入list型
        article_item["front_image_url"] = [front_img_url]
        article_item["vote_num"] = vote_num
        article_item["storeup_num"] = storeup_num
        article_item["comment_num"] = comment_num
        article_item["tags"] = tags_str
        article_item["content"] = content
        # 将item 传到 piplines
        yield article_item
