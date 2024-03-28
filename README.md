# 东方财富股吧爬虫

## 项目介绍

该项目使用 selenium 模拟用户操作抓取股吧发帖与评论信息（允许多线程同时抓取多支股票的相关信息），借助 stealth.min.js 隐藏浏览器的特征，将抓取到的数据储存到 MongoDB 中。

## 主要功能

1. 爬取指定股票股吧中的发帖信息，包括帖子标题，浏览量，评论数，帖子链接，发帖时间 (YYYY-MM-DD, HH: MM)，储存到数据库中。

2. 爬取指定时间范围中股吧帖子下的评论信息，包括评论内容，是一级或二级评论，点赞数，发帖时间 (YYYY-MM-DD, HH: MM)，储存到数据库中。

## 文件介绍

- `main.py` : 主程序，直接在里面调用函数即可开始抓取数据。

- `crawler.py` : 爬虫主体，包含了 `PostCrawler` 和 `CommentCrawler` 两个类，负责抓取帖子和评论的信息。

- `parser.py` : 解析器，包含了 `PostParser` 和 `CommentParser` 两个类，负责解析帖子和评论的网页源码。

- `mongodb.py` : 数据库接口，包含了 `MongoAPI` 类，负责建立与本地数据库的连接并实现基础操作。

- `stealth.min.js` : 一个 javascript 文件，用来抹掉 selenium 中的自动化特征。

## 爬取逻辑

## 使用步骤

### 1.下载代码

### 2.MongoDB安装，创建名为xxx的数据库

### 3.Webdriver安装

### 4.main中修改参数
