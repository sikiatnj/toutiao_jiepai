import json
import os
import re
from hashlib import md5
#from json.decoder import JSONDecodeError
from multiprocessing import Pool
from urllib import urlencode
import pymongo
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]


def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1,
    }
    params = urlencode(data)
    base = 'http://www.toutiao.com/search_content/'
    url = base + '?' + params
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        print('Error occurred')
        return None


def download_image(url):
    print('Downloading', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except ConnectionError:
        return None


def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def parse_image_details(text):
    try:
        data = json.loads(text)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                yield item.get('image_detail')
    except ValueError:
        pass


def get_page_detail(urls):
    try:
        if 'url' in urls:
            return urls.get('url')

    except ValueError:
        pass


def parse_page_detail(html):
    download_image(html)
    return {
        'url': html
    }


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('Successfully Saved to Mongo', result)
        return True
    return False


def main(offset):
    text = get_page_index(offset, KEYWORD)
    image_urls = parse_image_details(text)
    for url_list in image_urls:
        for url in url_list:
            uu = get_page_detail(url)
            print(uu)
            result = parse_page_detail(uu)
            if result: save_to_mongo(result)

if __name__=="__main__":
    pool = Pool(2)
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)
    pool.close()
    pool.join()
#if __name__=="__main__":
#    main(0)
