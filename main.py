from crawler import PostCrawler
from crawler import CommentCrawler
import threading
import time


def post_thread(stock_symbol, page):  # stock_symbol为股票的代码，page指想要爬取的帖子的页数（从第一页开始）
    post_crawler = PostCrawler(stock_symbol)
    post_crawler.crawl_post_info(page)


def comment_thread_date(stock_symbol, start_date, end_date):  # stock_symbol为股票的代码，date为想要爬取的日期范围
    comment_crawler = CommentCrawler(stock_symbol)
    comment_crawler.find_by_date(start_date, end_date)
    comment_crawler.crawl_comment_info()


def comment_thread_id(stock_symbol, start_id, end_id):  # stock_symbol为股票的代码，id是通过post_id来确定爬取，适合断联续爬
    comment_crawler = CommentCrawler(stock_symbol)
    comment_crawler.find_by_id(start_id, end_id)
    comment_crawler.crawl_comment_info()


if __name__ == "__main__":
    start_time = time.time()

    # 爬取发帖信息
    thread1 = threading.Thread(target=post_thread, args=('000799', 5))  # 设置想要爬取的股票代码和页数
    thread2 = threading.Thread(target=post_thread, args=('000729', 5))  # 可同时进行多个线程

    # 爬取评论信息，注意需先爬取发帖信息储存到数据库里后才可以爬取评论信息（因为需要用到第一步中的url）
    # thread1 = threading.Thread(target=comment_thread_date, args=('000651', '2020-01-01', '2023-12-31'))
    # thread2 = threading.Thread(target=comment_thread_date, args=('000651', '2020-01-01', '2023-12-31'))

    # thread1 = threading.Thread(target=comment_thread_id, args=('000651', 384942, 411959))
    # thread2 = threading.Thread(target=comment_thread_id, args=('000651', 62929, 321047))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    end_time = time.time()
    print(f"time cost: {end_time - start_time}")
