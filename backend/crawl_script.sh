#!/bin/bash

cd /home/dasol/product-review-service2/backend

/home/dasol/product-review-service2/backend/.venv/bin/python manage.py crawl_reviews >> /home/dasol/product-review-service2/logs/crawl.log 2>&1

#!/bin/bash
cd /home/dasol/product-review-service2/backend
/home/dasol/product-review-service2/backend/.venv/bin/python manage.py scheduled_crawl >> /home/dasol/product-review-service2/logs/crawl.log 2>&1
