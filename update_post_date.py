from mongodb_wrapper import MongoAPI


collection = MongoAPI('post_info', 'test1')
index_key = 'post_id'

for post_document in collection.find({}, {}):
    post_date_str = post_document["post_display_time"][:10]
    # print(post_document[index_key])
    collection.collection.update_one(
            {index_key: post_document[index_key]},
            { '$set': { "post_date": post_date_str} }
        )

exit(0)
