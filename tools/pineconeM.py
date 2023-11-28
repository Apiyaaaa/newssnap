import pinecone
import os
import openai
import asyncio


class PineconeM:
    def __init__(self):
        pinecone_key = os.getenv("PINECONE_KEY")
        pinecone.init(api_key=pinecone_key, environment="gcp-starter")
        lists_index = pinecone.list_indexes()
        if "newssnap-test" in lists_index:
            self.index = pinecone.Index("newssnap-test")
        else:
            pinecone.create_index("newssnap-test", shards=1, dimension=1536)
            self.index = pinecone.Index("newssnap-test")

    def insert(self, id, vector, metadata):
        try:
            record = self.index.fetch([id])['vectors']
            if len(record) > 0:
                pass
            else:
                self.index.upsert([(id, vector, metadata)])
        except Exception as e:
            print(e)
            return False

        return True

    def query(self, vector, k_top=10, filter=None, include_metadata=True, include_values=False):
        try:
            res = self.index.query(
                vector=vector,
                top_k=k_top,
                filter=filter,
                include_metadata=include_metadata, include_values=include_values)
        except Exception as e:
            print(e)
            return None

        return res
