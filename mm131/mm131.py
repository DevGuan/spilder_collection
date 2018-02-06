# -*- coding: utf-8 -*-
import requests
import queue
from bs4 import BeautifulSoup
from threading import Thread
import re
import os

category = ['xinggan', 'qingchun', 'xiaohua', 'chemo', 'qipao', 'mingxing']
# categoryStr = ['性感', '清纯', '校花', '车模', '旗袍', '明显']
baseUrl = 'http://www.mm131.com/{0}/'
r = re.compile('.*_(\d+).html')
queue = queue.Queue()
THREAD_NUM = 10
BASE_FILE_PATH = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36Name',
    'Referer': 'http://www.mm131.com/'}


def request(url, stream=False):
    try:
        response = requests.get(url, stream=stream, headers=headers)
        response.encoding = response.apparent_encoding
        if (response.status_code == 200):
            return response
    except Exception as e:
        print("访问失败{0},reason={1}".format(url, e))
    return None


class UrlContent(object):
    def __init__(self, url, type):
        self.url = url;
        self.type = type


class Worker(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        while (not queue.empty()):
            urlcontent = queue.get()
            self.down(urlcontent)
        print("队列全部完成")

    def down(self, urlcontent):

        try:
            if (urlcontent):
                response = request(urlcontent.url)
                if response:
                    bs = BeautifulSoup(response.content, 'html.parser')
                    dd = bs.select('dl.list-left.public-box')[0].find_all('dd')
                    for d in dd:
                        href = d.find('a')['href']
                        alt = d.find('img')['alt']
                        self.downImg(alt, href)
        except Exception as e:
            pass

    def downImg(self, title, href):
        path = os.path.join(BASE_FILE_PATH, title)
        if not os.path.isdir(path):
            os.mkdir(path)
        response = request(href)
        if response:
            bs = BeautifulSoup(response.content, 'html.parser', from_encoding='gb2312')
            pageNum = int(re.compile('共(\d+)页').match(bs.select('span.page-ch')[0].text).group(1))
            print("当前抓取{0},共有{1}张图片".format(title, pageNum))
            img = bs.select_one(".content-pic").find('img')
            self.saveImg(os.path.join(path, img['alt'] + '.jpg'), img['src'])
            for i in range(2, pageNum + 1):
                url = href.replace(".html", '_' + str(i) + '.html')
                response = request(url)
                if (response):
                    bs = BeautifulSoup(response.content, 'html.parser')
                    img = bs.select_one(".content-pic").find('img')
                    self.saveImg(os.path.join(path, img['alt'] + '.jpg'), img['src'])

    def saveImg(self, target_file, url):
        if os.path.isfile(target_file):
            print("{0}文件已存在本次不下载".format(target_file))
            return
        print("下载文件{0}".format(url))
        response = request(url)
        if (response):
            content = response.content
            with open(target_file, 'wb') as f:
                f.write(content)


class Command(object):
    def __init__(self):
        self.start()

    def start(self):
        for c in category:
            self.parseType(c)

    def parseType(self, type):
        try:
            url = baseUrl.format(type)
            print("解析页面{0}".format(url))
            response = requests.get(url)
            if (response.status_code == 200):
                bs = BeautifulSoup(response.content, 'html.parser')
                lastPage = bs.select(".page-en")[-1]['href']
                totalPage = int(r.match(lastPage).group(1))
                for page in range(1, totalPage + 1):
                    page = re.sub('\d+.html', str(page) + '.html', lastPage)
                    queue.put(UrlContent(baseUrl.format(type) + page, type))
        except Exception as e:
            print("访问{0}失败,reason={1}".format(type, e))


if __name__ == '__main__':
    BASE_FILE_PATH = os.path.join(os.getcwd(), 'mm131')
    if not os.path.isdir(BASE_FILE_PATH):
        os.mkdir(BASE_FILE_PATH)
    Command()
    for i in range(THREAD_NUM):
        worker = Worker().start()
