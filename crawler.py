from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random
import pandas as pd
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from datetime import datetime

from mongodb import MongoAPI
from guba_parser import PostParser
from guba_parser import CommentParser


EAST_MONEY_GUMA_URL_SCHEME = 'http://guba.eastmoney.com/list,%s,f_{%d}.html'
class PostCrawler(object):

    def __init__(self, stock_symbol: str):
        self._browser = None
        self._tick = stock_symbol
        self.start = time.time()  # calculate the time cost
        self._url_scheme = f'http://guba.eastmoney.com/list,{self._tick},f_%d.html'
        
    def _get_url_for_page(self, page_num):
        return self._url_scheme % page_num

    def _create_webdriver(self):
        options = webdriver.ChromeOptions()  # configure the webdriver
        options.add_argument('lang=zh_CN.UTF-8')
        options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                             'like Gecko) Chrome/111.0.0.0 Safari/537.36"')
        # options.add_argument("--headless=new")
        # options.add_argument("--window-size=1920,1080")
        self._browser = webdriver.Chrome(options=options)

        current_dir = os.path.dirname(os.path.abspath(__file__))  # hide the features of crawler/selenium
        js_file_path = os.path.join(current_dir, 'stealth.min.js')
        with open(js_file_path) as f:
            js = f.read()
        self._browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })

    def _get_max_page_num(self):
        # go to first page and get max page num
        if self._browser is None:
            self._create_webdriver()
        self._browser.get(self._get_url_for_page(1))
        page_element = self._browser.find_element(By.CSS_SELECTOR, 'ul.paging > li:nth-child(7) > a > span')
        return int(page_element.text)

    def cache_post_pages(self, page_begin, page_end):
        if (page_begin > page_end):
            print("Bad args: begin page number is larger than the end")
            return
        self._create_webdriver()
        max_page_num = self._get_max_page_num()
        if (page_end > max_page_num):
            print(f"Warning: end page number is larger than {max_page_num}, "\
                "will only go up to {max_page_num}")

        for page_num in range(page_begin, min(page_end + 1, max_page_num + 1)):
            url = self._get_url_for_page(page_num)
            for i in range(3):
                page_src = self._download_page_by_url(url)
                if page_src:
                    self._save_html_src(page_src, page_num)
                    break
                if i == 2:
                    print(f"tried 3 times and still unable to download {url}")

    def _download_page_by_url(self, url):
        time.sleep(abs(random.gauss(3, 1)))
        if self._browser is None:
            print("no webdriver created, please do and retry")
            return
        try:
            self._browser.get(url)
            return self._browser.page_source
        except Exception as e:
            print(f'unable to download {url}')
            time.sleep(0.01)
            self._browser.refresh()
            self._browser.delete_all_cookies()
            self._browser.quit()  # if we don't restart the webdriver, our crawler will be restricted access speed
            self._create_webdriver() # respawn
            return None

    def _save_html_src(self, page_src, page_num):
        with open(f"pages_cache/{page_num}.html", "w", encoding='utf-8') as f:
            f.write(page_src)

    def crawl_post_info(self, page1: int, page2: int):
        self._create_webdriver()
        max_page = self._get_max_page_num()  # confirm the maximum page number to crawl
        current_page = page1  # start page
        stop_page = min(page2, max_page)  # avoid out of the index

        parser = PostParser()  # must be created out of the 'while', as it contains the function about date
        date_str = datetime.today().strftime('%Y%m%d')
        postdb = MongoAPI('post_info', 
                          f'post_{self._tick}_{date_str}_{page1}_{stop_page}')  # connect the collection

        while current_page <= stop_page:  # use 'while' instead of 'for' is crucial for exception handling
            time.sleep(abs(random.gauss(3, 1)))  # random sleep time
            url = f'http://guba.eastmoney.com/list,{self._tick},f_{current_page}.html'

            try:
                self._browser.get(url)  # many times our crawler is restricted access (especially after 664 pages)
                dic_list = []
                list_items = self._browser.find_elements(By.CSS_SELECTOR, '.listitem')  # includes all posts on one page
                for li in list_items:  # get each post respectively
                    dic = parser.parse_post_info(li)
                    if 'guba.eastmoney.com' in dic['post_url']:  # other website is different!
                        dic_list.append(dic)
                    # else:
                    #     print(dic['post_url'])
                if dic_list:
                    postdb.insert_many(dic_list)
                else:
                    print(f"page {current_page} has nothing under guba.eastmoney.com")
                print(f'{self._tick}: 已经成功爬取第 {current_page} 页帖子基本信息，'
                      f'进度 {(current_page - page1 + 1)*100/(stop_page - page1 + 1):.2f}%')
                current_page += 1

            except Exception as e:
                print(f'{self._tick}: 第 {current_page} 页出现了错误 {e}')
                time.sleep(0.01)
                self._browser.refresh()
                self._browser.delete_all_cookies()
                self._browser.quit()  # if we don't restart the webdriver, our crawler will be restricted access speed
                self._create_webdriver()  # restart it again!

        end = time.time()
        time_cost = end - self.start  # calculate the time cost
        start_date = postdb.find_last()['post_date']
        end_date = postdb.find_first()['post_date']  # get the post time range
        # end_date = mongodb.find_one({}, {'_id': 0, 'post_date': 1})['post_date']  # first post is hottest not newest
        row_count = postdb.count_documents()
        self._browser.quit()

        print(f'成功爬取 {self._tick}股吧共 {stop_page - page1 + 1} 页帖子，总计 {row_count} 条，花费 {time_cost/60:.2f} 分钟')
        print(f'帖子的时间范围从 {start_date} 到 {end_date}')


class CommentCrawler(object):

    def __init__(self, stock_symbol: str):
        self.browser = None
        self.symbol = stock_symbol
        self.start = time.time()
        self.post_df = None  # dataframe about the post_url and post_id
        self.current_num = 0

    def create_webdriver(self):
        options = webdriver.ChromeOptions()  # configure the webdriver
        options.add_argument('lang=zh_CN.UTF-8')
        options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                             'like Gecko) Chrome/111.0.0.0 Safari/537.36"')
        self.browser = webdriver.Chrome(options=options)
        # self.browser.set_page_load_timeout(2)  # set the timeout restrict

        current_dir = os.path.dirname(os.path.abspath(__file__))  # hide the features of crawler/selenium
        js_file_path = os.path.join(current_dir, 'stealth.min.js')
        with open(js_file_path) as f:
            js = f.read()
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })

    def find_by_date(self, start_date, end_date):
        # get comment urls through date (used for the first crawl)
        """
        :param start_date: '2003-07-21' 字符串格式 ≥
        :param end_date: '2024-07-21' 字符串格式 ≤
        """
        postdb = MongoAPI('post_info', f'post_{self.symbol}')
        time_query = {
            'post_date': {'$gte': start_date, '$lte': end_date},
            'comment_num': {'$ne': 0}  # avoid fetching urls with no comment
        }
        post_info = postdb.find(time_query, {'_id': 1, 'post_url': 1})  # , 'post_date': 1
        self.post_df = pd.DataFrame(post_info)

    def find_by_id(self, start_id: int, end_id: int):
        # get comment urls through post_id (used when crawler is paused accidentally) crawl in batches
        """
        :param start_id: 721 整数 ≥
        :param end_id: 2003 整数 ≤
        """
        postdb = MongoAPI('post_info', f'post_{self.symbol}')
        id_query = {
            '_id': {'$gte': start_id, '$lte': end_id},
            'comment_num': {'$ne': 0}  # avoid fetching urls with no comment
        }
        post_info = postdb.find(id_query, {'_id': 1, 'post_url': 1})  # , 'post_date': 1
        self.post_df = pd.DataFrame(post_info)

    def crawl_comment_info(self):
        url_df = self.post_df['post_url']
        id_df = self.post_df['_id']
        total_num = self.post_df.shape[0]

        self.create_webdriver()
        parser = CommentParser()
        commentdb = MongoAPI('comment_info', f'comment_{self.symbol}')

        for url in url_df:
            try:
                time.sleep(abs(random.normalvariate(0.03, 0.01)))  # random sleep time

                try:  # sometimes the website needs to be refreshed (situation comment is loaded unsuccessfully)
                    self.browser.get(url)  # this function may also get timeout exception
                    WebDriverWait(self.browser, 0.2, poll_frequency=0.1).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.reply_item.cl')))
                except TimeoutException:  # timeout situation
                    self.browser.refresh()
                    print('------------ refresh ------------')
                finally:
                    reply_items = self.browser.find_elements(By.CSS_SELECTOR, 'div.allReplyList > div.replylist_content > div.reply_item.cl')  # some have hot reply list avoid fetching twice

                dic_list = []  # as batch insert is more efficient than insert one
                for item in reply_items:
                    dic = parser.parse_comment_info(item, id_df.iloc[self.current_num].item())
                    # save the related post_id
                    dic_list.append(dic)

                    if parser.judge_sub_comment(item):  # means it has sub-comments
                        sub_reply_items = item.find_elements(By.CSS_SELECTOR, 'li.reply_item_l2')

                        for subitem in sub_reply_items:
                            dic = parser.parse_comment_info(subitem, id_df.iloc[self.current_num].item(), True)
                            # as it has sub-comments
                            dic_list.append(dic)

                commentdb.insert_many(dic_list)
                self.current_num += 1
                print(f'{self.symbol}: 已成功爬取 {self.current_num} 页评论信息，进度 {self.current_num*100/total_num:.3f}%')

            except TypeError as e:  # some comment is not allowed to display, just skip it
                self.current_num += 1
                print(f'{self.symbol}: 第 {self.current_num} 页出现了错误 {e} （{url}）')  # maybe the invisible comments
                print(f'应爬取的id范围是 {id_df.iloc[0]} 到 {id_df.iloc[-1]}, id {id_df.iloc[self.current_num - 1]} 出现了错误')
                self.browser.delete_all_cookies()
                self.browser.refresh()
                self.browser.quit()  # restart webdriver if crawler is restricted
                self.create_webdriver()

        end = time.time()
        time_cost = end - self.start
        row_count = commentdb.count_documents()
        self.browser.quit()
        print(f'成功爬取 {self.symbol}股吧 {self.current_num} 页评论，共 {row_count} 条，花费 {time_cost/60:.2f}分钟')
