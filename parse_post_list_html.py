import json
import logging
import pathlib
import pymongo
import re
import sys

from mongodb_wrapper import MongoAPI

class PostHtmlParser:
    def __init__(self):
        self._post_list_pattern = re.compile(
                '</script></div></div><script>var article_list=(.+);    var other_list'
            )
        self._post_keys = ['post_id', 'post_title', 'post_comment_count', 
             'user_id', 'post_source_id', 'post_type', 'post_display_time']

    def _get_json_from_str(self, line_in):
        match = self._post_list_pattern.match(line_in)
        if match is None:
            return None
        return match.group(1)

    def _parse_post_items_from_json(self, str_in):
        article_list = json.loads(str_in)
        posts = article_list['re']
        return [
                {key: post_item[key] for key in self._post_keys} for post_item in posts
            ]

    def parse_html_doc_for_post_items(self, html_doc):
        for line in html_doc:
            matched_str = self._get_json_from_str(line)
            if matched_str:
                return self._parse_post_items_from_json(matched_str)
        return None

class PostsWriter:
    def __init__(self, collection, index_name):
        self._collection = collection
        self._index_name = index_name
        self._collection.create_index(
            [(self._index_name, pymongo.DESCENDING)]
        )
        self._logger = logging.getLogger("PostWriter")

    def _is_post_in_collection(self, post_item):
        return self._collection.find_one(
            {self._index_name: post_item[self._index_name]}, {}) is not None

    def write_posts(self, post_items):
        if post_items is None:
            self._logger.warning("nothing to write")
            return
        posts_to_write = [
                post for post in post_items if not self._is_post_in_collection(post)
            ]
        if not posts_to_write:
            self._logger.warning("no new posts to write")
            return
        self._collection.insert_many(posts_to_write)

def parse_and_write(parser, writer, logger, html_doc):
    posts_items = parser.parse_html_doc_for_post_items(html_doc)
    if not posts_items:
        logger.error("parser found no posts")
        return False
    writer.write_posts(posts_items)
    return True

if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger("parse_post_list_html")
    logger.setLevel(logging.INFO)
    if len(sys.argv) != 5:
        print("Please provide db name, collection name, index name" \
              " and dir of html files")
        exit(10)
    html_dir = pathlib.Path(sys.argv[4])
    if not html_dir.is_dir():
        print(f"directory {str(html_dir)} not found")
        exit(20)
    
    post_parser = PostHtmlParser()
    postdb = MongoAPI(sys.argv[1], sys.argv[2])
    writer = PostsWriter(postdb.collection, sys.argv[3])

    for html_file in html_dir.glob('./*.html'):
        with html_file.open(encoding='utf-8') as f:
            parse_and_write(post_parser, writer, logger, f)
            logger.info(f"{str(html_file)} done")
