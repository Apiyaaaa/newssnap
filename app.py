from tools.myOpenai import MyOpenAI
from tools.rssParser import RssParser
from dbM import MyMongo, RedisHelper
import asyncio
import time
from dotenv import load_dotenv
import os
import openai
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
redis = RedisHelper()
openai.api_key = os.getenv("OPENAI_API_KEY")
# 配置信号量
semaphore = 5
# 配置rss链接
# TODO: 从数据库中读取 以后再说
# def get_rss_links():
#     rss_links = mongo.db['rss'].find({'status': 'active'})
#     rss_links = {link['name']: link['link'] for link in rss_links}
#     return rss_links

rss_links = {
    '极客公园': 'https://www.geekpark.net/rss',
    '36氪 - 24小时热榜': 'https://rsshub.app/36kr/hot-list',
    '新华社新闻': 'https://rsshub.app/news/whxw',
    '新浪科技 - 科学探索': 'https://rsshub.app/sina/discovery/zx',
    '新浪滚动新闻': 'https://rsshub.app/sina/rollnews',
    '今日关注 - 网易新闻': 'https://rsshub.app/163/today',
    '财富中文网': 'https://rsshub.app/fortunechina',
    '少数派 -- 首页': 'https://rsshub.app/sspai/index',
}


# 计算本次花费
cost = 0
news_count = 0

# 用于处理新闻的协程


async def process_news(news, mongo, redis, semaphore):
    global cost, news_count
    print('开始处理', news['link'])
    try:
        async with semaphore:
            myopenai = MyOpenAI(news['content'])
            e_s_object = await myopenai.aget_Object()
            cost += myopenai.total_cost()
        news['ai_summary'] = e_s_object['summary']
        news['embedding'] = e_s_object['embedding']
    except Exception as e:
        redis.r.rpush('waiting_news', str(news))
        print(e, '重新加入队列', news['link'])
        return
    mongo.saveNews(collection='news', news=news)
    news_count += 1


# 用于加载新闻的函数
def load_news(redis, mongo, rss_links):
    for link in rss_links:
        parse = RssParser(rss_links[link])
        parse.parse()
        for news in parse.news:
            news_data = news.get()
            if not mongo.db['news'].find_one({'link': news_data['link']}):
                redis.r.rpush('waiting_news', str(news_data))
    print('redis填充成功', '共', redis.r.llen('waiting_news'), '条新闻')

# 用于处理新闻的函数


async def news_processor(redis, mongo, semaphore):
    semaphore = asyncio.Semaphore(semaphore)
    tasks = []
    while redis.r.llen('waiting_news') > 0:
        news = redis.r.lpop('waiting_news')
        news = eval(news)
        task = asyncio.create_task(process_news(news, mongo, redis, semaphore))
        tasks.append(task)
        if len(tasks) >= 10:
            await asyncio.gather(*tasks)
            tasks = []
    await asyncio.gather(*tasks)


def main():
    # 清空数据库 如果需要持续化就禁用
    start = time.time()
    # redis.clean()
    print(redis.r.keys())
    # 加载新闻
    load_news(redis, mongo, rss_links)
    # 处理新闻 获取摘要和embedding
    asyncio.run(news_processor(redis, mongo, semaphore))
    print('本次估计花费：', cost)
    time_to_min = cost / 1000 / 60
    print('本次处理时间为：', time_to_min, '分钟')
    print('共处理', news_count, '条新闻')


if __name__ == "__main__":
    main()
