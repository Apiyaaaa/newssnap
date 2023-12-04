from tools.myOpenai import MyOpenAI
from tools.rssParser import RssParser
from dbM import MyMongo
import asyncio
import time
from dotenv import load_dotenv
import os
import openai
from collections import deque
import logging
# 加载环境变量
load_dotenv()

if os.getenv("OPENAI_API_KEY") is None:
    raise Exception('OPENAI_API_KEY is None')
if os.getenv("MONGODB_URI") is None:
    raise Exception('MONGODB_URI is None')
if os.getenv("PINECONE_KEY") is None:
    raise Exception('PINECONE_KEY is None')


# 配置数据库
mongo = MyMongo()
openai.api_key = os.getenv("OPENAI_API_KEY")
# 配置信号量
semaphore = 5

# 配置rss链接
def get_rss_links():
    rss_links = mongo.db['rss'].find({'status': 'active'})
    rss_links = {link['name']: link['link'] for link in rss_links}
    return rss_links

rss_links = get_rss_links()


# 计算本次花费
cost = 0
news_count = 0
waiting_news = deque()
# 用于处理新闻的协程

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
logging.getLogger('openai').setLevel(logging.WARNING)

async def process_news(news, mongo, semaphore):
    global cost, news_count
    logging.info(f'开始处理新闻 {news["link"]}')
    try:
        async with semaphore:
            myopenai = MyOpenAI(news['content'])
            e_s_object = await myopenai.aget_Object()
            cost += myopenai.total_cost()
        news['ai_summary'] = e_s_object['summary']
        news['embedding'] = e_s_object['embedding']
    except Exception as e:
        waiting_news.append(news)
        logging.warning(f'处理新闻 {news["link"]} 失败')
        return
    mongo.saveNews(collection='news', news=news)
    news_count += 1
    logging.info(f'处理新闻 {news["link"]} 完成， 共花费 {myopenai.total_cost()}')


# 用于加载新闻的函数
def load_news(mongo, rss_links):
    for link in rss_links:
        logging.info(f'开始加载 {link}')
        parse = RssParser(rss_links[link], link)
        parse.parse()
        for news in parse.news:
            news_data = news.get()
            if not mongo.db['news'].find_one({'link': news_data['link']}):
                waiting_news.append(news_data)

# 用于处理新闻的函数


async def news_processor(mongo, semaphore):
    semaphore = asyncio.Semaphore(semaphore)
    tasks = []
    while len(waiting_news) > 0:
        news = waiting_news.popleft()
        task = asyncio.create_task(process_news(news, mongo, semaphore))
        tasks.append(task)
        if len(tasks) >= 10:
            await asyncio.gather(*tasks)
            tasks = []
    await asyncio.gather(*tasks)


def main():
    logging.info('开始处理新闻')
    start = time.time()

    # 加载新闻
    load_news(mongo, rss_links)
    logging.info(f'加载新闻完成 共 {len(waiting_news)} 条新闻')
    # 处理新闻 获取摘要和embedding
    asyncio.run(news_processor(mongo, semaphore))
    logging.info(f'处理新闻完成 共 {news_count} 条新闻')
    time_to_min = (time.time() - start) / 60
    logging.info(f'总花费 {cost}')
    logging.info(f'总耗时 {time_to_min} 分钟')


if __name__ == "__main__":
    main()
