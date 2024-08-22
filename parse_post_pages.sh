#!/bin/bash

for file in ./pages_cache/*.html; do
    python3 parse_post_list_html.py post_info test1 post_id ${file}
    echo ${file}
done