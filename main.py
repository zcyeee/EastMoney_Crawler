from crawler import PostCrawler
from crawler import CommentCrawler
import threading

import sys

def post_thread(stock_symbol, start_page, end_page):  # stock_symbol为股票的代码，page为想要爬取的页面范围
    post_crawler = PostCrawler(stock_symbol)
    post_crawler.crawl_post_info(start_page, end_page)

def dl_post_thread(stock_symbol, start_page, end_page):  # stock_symbol为股票的代码，page为想要爬取的页面范围
    post_crawler = PostCrawler(stock_symbol)
    post_crawler.cache_post_pages(start_page, end_page)

def comment_thread_date(stock_symbol, start_date, end_date):  # stock_symbol为股票的代码，date为想要爬取的日期范围
    comment_crawler = CommentCrawler(stock_symbol)
    comment_crawler.find_by_date(start_date, end_date)
    comment_crawler.crawl_comment_info()


def comment_thread_id(stock_symbol, start_id, end_id):  # stock_symbol为股票的代码，id是通过post_id来确定爬取，适合断联续爬
    comment_crawler = CommentCrawler(stock_symbol)
    comment_crawler.find_by_id(start_id, end_id)
    comment_crawler.crawl_comment_info()


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Please provide start and end page numbers as positional args")
        exit(1)
    # 爬取发帖信息
    begin_page_number = int(sys.argv[1])
    end_page_number = int(sys.argv[2])
    if (begin_page_number > end_page_number):
        print("Bad args: begin page number is larger than the end")
        exit(2)
    # thread1 = threading.Thread(target=post_thread, 
    #                            args=('zssh000001', begin_page_number, end_page_number))  # 设置想要爬取的股票代码，开始与终止页数
    thread1 = threading.Thread(target=dl_post_thread, 
                               args=('zssh000001', begin_page_number, end_page_number))  # 设置想要爬取的股票代码，开始与终止页数
    # thread2 = threading.Thread(target=post_thread, args=('000729', 1, 500))  # 可同时进行多个线程

    # 爬取评论信息，注意需先爬取发帖信息储存到数据库里后才可以爬取评论信息（因为需要用到第一步中的url）
    # thread1 = threading.Thread(target=comment_thread_date, args=('000333', '2020-01-01', '2023-12-31'))
    # thread2 = threading.Thread(target=comment_thread_date, args=('000729', '2020-01-01', '2023-12-31'))

    # 中断之后重新通过_id接着爬取
    # thread1 = threading.Thread(target=comment_thread_id, args=('000651', 384942, 411959))
    # thread2 = threading.Thread(target=comment_thread_id, args=('000651', 62929, 321047))

    thread1.start()
    # thread2.start()

    thread1.join()
    # thread2.join()

    print(f"you have fetched data successfully, congratulations!")
