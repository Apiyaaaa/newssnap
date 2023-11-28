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
