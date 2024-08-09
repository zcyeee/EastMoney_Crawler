from collections import deque
import pymongo
import re
import sys

from mongodb import MongoAPI

class CollectionMerger:
    def __init__(self, db_name, source_collection_name, dest_collection_name):
        if (source_collection_name == dest_collection_name):
            raise ValueError("source and dest collections identical")
        self._source_collection = MongoAPI(db_name, source_collection_name)
        self._dest_collection = MongoAPI(db_name, dest_collection_name)
        self._add_index() # detect collisions faster
        # regex to extract page id from url
        self._post_id_match_prog = re.compile(
            ",([0-9]+)\.html"
        )
        self._bulk_write_size = 1000
        self._posts_to_write = deque()
        self._post_ids_to_write = {}

        self._collision_count = 0
    
    def _record_collision(self):
        self._collision_count += 1

    def _clear_buffers(self):
        self._posts_to_write.clear()
        self._post_ids_to_write = {}

    def _is_write_queue_full(self):
        return len(self._posts_to_write) == self._bulk_write_size

    def _inject_post_item_to_write_queue(self, post_item):
        if "post_id" not in post_item:
            print("post item does not have an ID. Nothing written")
            return False
        post_id_to_write = post_item["post_id"]
        if post_id_to_write in self._post_ids_to_write:
            print(f"collision with post id {post_id_to_write}, in buffer")
            self._record_collision()
            return False
        self._post_ids_to_write[post_id_to_write] = True
        self._posts_to_write.append(post_item)
        return True
    
    def _flush_queue_to_dest(self):
        if len(self._posts_to_write) == 0:
            print("Buffer is empty, nothing to write")
            return
        self._dest_collection.insert_many(self._posts_to_write)
        self._clear_buffers()

    # wrapper with bulk write
    def _write_post_to_dest(self, post_item):
        if self._is_write_queue_full():
            self._flush_queue_to_dest()
        self._inject_post_item_to_write_queue(post_item)

    def _add_index(self):
        self._dest_collection.collection.create_index(
            [("post_id", pymongo.DESCENDING)]
        )

    def source_to_dest(self):
        # drop _id
        for idx, post_document in enumerate(
                self._source_collection.find({}, {"_id": False})
            ):
            match_result = self._post_id_match_prog.search(
                post_document["post_url"]
            )
            post_id = int(match_result.group(1))
            # assuming page ID from url is unique
            if self._dest_collection.find_one({"post_id": post_id}, {}) is not None:
                print(f"item {idx} collision with post id {post_id}")
                self._record_collision()
            else:
                post_document["post_id"] = post_id
                self._write_post_to_dest(post_document)
        # final touch -- flush anything that's left in the buffers
        self._flush_queue_to_dest()
        print(f"total number of collisions: {self._collision_count}")

# TODO add datetime

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Please provide db name, source collection name" \
              " and target collection name")
        exit(10)
    merger = CollectionMerger(sys.argv[1], sys.argv[2], sys.argv[3])
    merger.source_to_dest()
    exit(0)
