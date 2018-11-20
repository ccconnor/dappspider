# -*- coding: utf-8 -*-

import time
import re
from settings import *
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import TimeoutException


class DappSpider:
    name = 'dapp'
    request_url = 'https://dapp.review/explore/eos'
    dapp_list = []

    def open_spider(self):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        self.browser = webdriver.Chrome(options=chrome_options)
        # self.browser.implicitly_wait(10)
        # self.browser.set_page_load_timeout(10)
        # self.browser.set_script_timeout(10)

    def close_spider(self):
        self.browser.quit()

    def run_spider(self):
        # self.browser.maximize_window()
        self.browser.get(self.request_url)
        time.sleep(3)

        # 模拟鼠标滚动
        # pos = 0
        # for i in range(1500):
        #     pos += i * 500
        #     js = "document.documentElement.scrollTop=%d" % pos
        #     self.browser.execute_script(js)

        self.get_dapp_list()
        self.get_official_site()

    def get_dapp_list(self):
        current_time = int(time.time())
        dapp_types = self.browser.find_elements_by_tag_name('small')
        for i in range(len(dapp_types)):
            dapp_info = dict()
            dapp_info['time'] = current_time
            dapp_info['name'] = dapp_types[i].find_element_by_xpath('..//..//h2').text
            dapp_info['type'] = dapp_types[i].text
            dapp_info['dau'] = int(re.sub('[,]', '', dapp_types[i].find_element_by_xpath('..//..//..//span[2]').text))
            dapp_info['txAmount'] = float(re.sub('[,]', '', dapp_types[i].find_element_by_xpath('..//..//..//div[4]//div//p[2]//span[2]').text))
            dapp_info['txCount'] = int(re.sub('[,]', '', dapp_types[i].find_element_by_xpath('..//..//..//div[4]//div//p[3]//span[2]').text))
            dapp_info['url'] = dapp_types[i].find_element_by_xpath('..//..//a').get_attribute("href")
            # noinspection PyBroadException
            try:
                dapp_info['icon'] = dapp_types[i].find_element_by_xpath('..//..//../img').get_attribute("src")
            except Exception as e:
                print('Error:', e)
                dapp_info['icon'] = ''
            self.dapp_list.append(dapp_info)

    def get_official_site(self):
        for i in range(len(self.dapp_list)):
            self.browser.get(self.dapp_list[i]['url'])
            time.sleep(1)

            # noinspection PyBroadException
            try:
                title = self.browser.find_element_by_tag_name('h2')
                official_site = title.find_element_by_xpath('../a').get_attribute("href")
            except Exception as e:
                print('Error:', e)
                official_site = ''
            self.dapp_list[i]['officialSite'] = official_site
            print(i)

    def process_items(self):
        client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
        collection = client['app_db']['dapp_info']
        for dapp in self.dapp_list:
            dapp['officialSite'] = DappSpider.strip_ref(dapp['officialSite'])
            client['app_db']['dapp_history'].insert_one(dapp)
            dapp_filter = {'name': dapp['name']}
            result = collection.find_one(dapp_filter)
            if result is not None:
                dapp['_id'] = result['_id']
                dapp['reviewed'] = result['reviewed']
            else:
                dapp['reviewed'] = False
            collection.replace_one(dapp_filter, dapp, True)
        client.close()

    @staticmethod
    def strip_ref(url):
        key_list = ('?', '/a/', '/i/', '/r/', '/dappreview23')
        for key in key_list:
            url = url.partition(key)[0]
        return url


def main():
    dapp_spider = DappSpider()
    dapp_spider.open_spider()
    dapp_spider.run_spider()
    dapp_spider.close_spider()
    dapp_spider.process_items()


if __name__ == "__main__":
    main()
