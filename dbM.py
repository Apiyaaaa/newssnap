import redis
import datetime
from pymongo.mongo_client import MongoClient
import os

class MyMongo:
    def __init__(self) -> None:
        self.connect_str = os.getenv("MONGODB_URI")
        self.client = MongoClient(self.connect_str)
        self.db = self.client["NewsSnap"]
        # self.collection = None

    def saveNews(self, collection, news):
        if not collection or not news or not isinstance(news, dict) or 'link' not in news:
            return False
        try:
            return self.db[collection].update_one({'link': news['link']}, {'$setOnInsert': news}, upsert=True)
        except Exception as e:
            print(e)
            return False


class RedisHelper():
    def formatTime(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self):
        self.r = redis.StrictRedis(
            host='localhost', port=6379, db=0, decode_responses=True, charset='utf-8')
        print(self.formatTime(), 'redis连接成功')

    def clean(self):
        self.r.flushdb()
        print(self.formatTime(), 'redis清空成功')
