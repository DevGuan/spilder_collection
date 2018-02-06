# -*- coding: utf-8 -*-
import re, os, queue, time
from bs4 import BeautifulSoup
import requests
from threading import Thread

BBS__URL = 'http://93.t9p.today/{0}'
BASE_URL = 'http://93.t9p.today/forumdisplay.php?fid={0}'
URL_LIST = [19,21]
PARSER = 'html.parser'
# 线程数量
THREAD_NUMBER = 10
queue = queue.Queue()
BASE_PATH = None


def request(url, stream=False):
    response = requests.get(url, stream=stream)
    response.encoding = response.apparent_encoding
    if (response.status_code == 200):
        return response
    return None


class Content(object):
    def __init__(self, url, title):
        self.url = url
        self.title = title.strip()
        # self.category = category


class Worker(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while (True):
            try:
                content = queue.get(timeout=10)
                self.work(content)
            except Exception as e:
                time.sleep(10)
                continue

    def work(self, content):
        if content:
            bbsurl = BBS__URL.format(content.url)
            response = requests.get(bbsurl)
            if (response):
                try:
                    bs = BeautifulSoup(response.content, PARSER)
                    path = os.path.join(BASE_PATH, content.title)
                    if not os.path.isdir(path):
                        os.mkdir(path)
                    pageNum = self.getPage(bs)
                    self.parseBbsPage(bbsurl, path)
                    for i in range(2, pageNum):
                        self.parseBbsPage(bbsurl + '&page' + str(i), path)
                except Exception as e:
                    print("抓取失败{0},reason={1}".format(content.url, e))

    def parseBbsPage(self, url, path):
        response = requests.get(url)
        if (response):
            bs = BeautifulSoup(response.content, PARSER)
            for post in bs.select("#postlist"):
                postdiv = post.find('div')
                if postdiv:
                    t_msgfontfix = postdiv.select_one('.t_msgfontfix')
                    if (t_msgfontfix):
                        for img in t_msgfontfix.find_all(file=attachments):
                            src = img['file']
                            url = BBS__URL.format(src)
                            self.downImg(url, os.path.join(path, src.split('/')[-1]))

    def downImg(self, url, targer_file):
        print("开始下载文件,地址为{0}".format(url))
        if os.path.isfile(targer_file):
            print("文件已存在,本次不下载")
            return
        with open(targer_file, 'wb') as f:
            f.write(requests.get(url).content)

    def getPage(self, bs):
        pageNum = 1
        try:
            if (bs.select_one('a.last')):
                pageNum = int(re.match(re.compile(('.* (\d+)')), bs.select('a.last')[-1].text).group(1))
            else:
                pageNum = int(bs.select_one('div.pages').find_all("a")[-1].text)
        except:
            pass
        return pageNum

#校验是否有权限访问栏目
def validateAnymouns(url):
    print("开始校验访问权限{0}".format(url))
    response = request(url)
    if (response):
        bs = BeautifulSoup(response.content, PARSER)
        if (not bs.select_one('div.postbox')):
            return True
    return False


def parsePages(url):
    response = requests.get(url)
    if (response):
        bs = BeautifulSoup(response.content, PARSER)
        addUrlToQueue(url)
        pageNum=getPage(bs)
        print("开始解析帖子列表当前板块id={0},总页数{1}".format(url, pageNum))
        if (pageNum > 2):
            for i in range(2, pageNum):
                addUrlToQueue(url + '&page=' + str(i))


def getPage(bs):
    pageNum = 1
    try:
        if (bs.select_one('a.last')):
            pageNum = int(re.match(re.compile(('.* (\d+)')), bs.select('a.last')[-1].text).group(1))
        else:
            pageNum = int(bs.select_one('div.pages').find_all("a")[-1].text)
    except:
        pass
    return pageNum


def addUrlToQueue(url):
    response = requests.get(url)
    if (response):
        bs = BeautifulSoup(response.content, PARSER)
        content_list = bs.find_all(id=r)
        for t in content_list:
            subject = t.select_one('.subject')
            print("增加url到队列{0}".format(subject.find('a')['href']))
            queue.put(Content(subject.find('a')['href'], subject.find('a').text))


attachments = re.compile('attachments/(.*)')
if __name__ == '__main__':
    BASE_PATH = os.path.join(os.getcwd(), '91photo')
    if not os.path.isdir(BASE_PATH):
        os.mkdir(BASE_PATH)
    for id in URL_LIST:
        if not validateAnymouns(BASE_URL.format(id)):
            URL_LIST.remove(id)

    for i in range(THREAD_NUMBER):
        Worker().start()

    r = re.compile(".*normalthread_\d+.*")
    for url in URL_LIST:
        parsePages(BASE_URL.format(id))
