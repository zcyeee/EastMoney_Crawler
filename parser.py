from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime
import re


class PostParser(object):

    def __init__(self):
        self.year = None
        self.month = 13
        self.id = 0

    @staticmethod
    def parse_post_title(html):
        title_element = html.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div')
        return title_element.text

    @staticmethod
    def parse_post_view(html):
        view_element = html.find_element(By.CSS_SELECTOR, 'td > div')
        return view_element.text  # stay as str structure! as character like '万' exist

    @staticmethod
    def parse_comment_num(html):
        num_element = html.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div')
        try:
            comment_num = int(num_element.text)  # be converted to int
        except:
            comment_num = int(float(num_element.text[:-1]) * 10000)  # 有时评论个数会过'万'
        return comment_num

    @staticmethod
    def parse_post_url(html):
        url_element = html.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > a')
        return url_element.get_attribute('href')

    @staticmethod
    def remove_char(date_str):
        # 使用正则表达式去掉所有汉字字符（处理日期中包含“修改”字符的情况）
        cleaned_str = re.sub(r'[^\d\s:-]', '', date_str)
        return cleaned_str.strip()

    def get_post_year(self, html):
        post_url = self.parse_post_url(html)
        driver = webdriver.Chrome()

        if 'guba.eastmoney.com' in post_url:  # 这是绝大部分的普通帖子
            driver.get(post_url)
            date_str = driver.find_element(By.CSS_SELECTOR, 'div.newsauthor > div.author-info.cl > div.time').text
            self.year = int(self.remove_char(date_str)[:4])
            driver.quit()
        elif 'caifuhao.eastmoney.com' in post_url:  # 有些热榜帖子会占据第一位，对于这种情况要特殊处理
            driver.get(post_url)
            date_str = driver.find_element(By.CSS_SELECTOR, 'div.article.page-article > div.article-head > '
                                                            'div.article-meta > span.txt').text
            self.year = int(self.remove_char(date_str)[:4])
            driver.quit()
        else:
            self.year = datetime.now().year

    @staticmethod
    def judge_post_date(html):  # eastmoney has several fucking inaccurate display dates
        try:
            judge_element = html.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > span')
            if judge_element.text == '问董秘':  # is not None
                return False
        except:
            return True

    def parse_post_date(self, html):
        try:
            time_element = html.find_element(By.CSS_SELECTOR, 'div.update.pub_time')
            time_str = time_element.text
            month, day = map(int, time_str.split(' ')[0].split('-'))
        except Exception as e:  # some post is different, just ignore it (very seldom)
            print('Fail to find the date of the post.', '\n', '{}'.format(e))
            return None, None

        if self.judge_post_date(html):
            if self.month < month == 12:
                self.year -= 1
            self.month = month

        if self.year is None:  # get the post year through exact post_url
            self.get_post_year(html)

        date = f'{self.year}-{month:02d}-{day:02d}'
        time = time_str.split(' ')[1]
        return date, time

    @staticmethod
    def parse_post_author(html):
        author_element = html.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > div')
        return author_element.text

    def parse_post_info(self, html):
        self.id += 1
        title = self.parse_post_title(html)
        view = self.parse_post_view(html)
        num = self.parse_comment_num(html)
        url = self.parse_post_url(html)
        date, time = self.parse_post_date(html)
        author = self.parse_post_author(html)
        post_info = {
            '_id': self.id,
            'post_title': title,
            'post_view': view,
            'comment_num': num,
            'post_url': url,
            'post_date': date,
            'post_time': time,
            'post_author': author
        }
        return post_info


class CommentParser(object):

    @staticmethod
    def judge_sub_comment(html):  # identify whether it has sub-comments
        sub = html.find_elements(By.CSS_SELECTOR, 'ul.replyListL2')  # must use '_elements' instead of '_element'
        return bool(sub)  # if not null return True, vice versa, return False

    @staticmethod
    def parse_comment_content(html, sub_bool):
        if sub_bool:  # situation to deal with sub-comments
            content_element = html.find_element(By.CSS_SELECTOR, 'div.reply_title > span')
        else:
            content_element = html.find_element(By.CSS_SELECTOR, 'div.recont_right.fl > div.reply_title > span')
        return content_element.text

    @staticmethod
    def parse_comment_like(html, sub_bool):
        if sub_bool:  # situation to deal with sub-comments
            like_element = html.find_element(By.CSS_SELECTOR, 'span.likemodule')
        else:
            like_element = html.find_element(By.CSS_SELECTOR, 'ul.bottomright > li:nth-child(4) > span')

        if like_element.text == '点赞':  # website display text instead of '0'
            return 0
        else:
            return int(like_element.text)

    @staticmethod
    def parse_comment_date(html, sub_bool):
        if sub_bool:  # situation to deal with sub-comments
            date_element = html.find_element(By.CSS_SELECTOR, 'span.pubtime')
        else:
            date_element = html.find_element(By.CSS_SELECTOR, 'div.publishtime > span.pubtime')
        date_str = date_element.text
        date = date_str.split(' ')[0]
        time = date_str.split(' ')[1][:5]
        return date, time

    def parse_comment_info(self, html, post_id, sub_bool: bool = False):  # sub_pool is used to distinguish sub-comments
        content = self.parse_comment_content(html, sub_bool)
        like = self.parse_comment_like(html, sub_bool)
        date, time = self.parse_comment_date(html, sub_bool)
        whether_subcomment = int(sub_bool)  # '1' means it is sub-comment, '0' means it is not
        comment_info = {
            'post_id': post_id,
            'comment_content': content,
            'comment_like': like,
            'comment_date': date,
            'comment_time': time,
            'sub_comment': whether_subcomment,
        }
        return comment_info
