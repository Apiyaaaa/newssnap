import feedparser
import markdownify
from bs4 import BeautifulSoup as bs
from time import mktime


class News:
    # if none assign default value
    def __init__(self, title, link, content=None, source=None, date=None, author=None, ai_summary=None) -> None:
        self.title = title
        self.link = link
        self.content = markdownify.markdownify(str(content))
        self.source = source
        self.date = date
        self.author = author
        self.ai_summary = ai_summary
        self.embedding = None

    def get(self):
        return {
            'title': self.title,
            'link': self.link,
            'content': self.content,
            'source': self.source,
            'date': self.date,
            'author': self.author,
            'ai_summary': self.ai_summary,
            'embedding': self.embedding
        }


class RssParser:
    def __init__(self, url, source) -> None:
        self.url = url
        self.entries = None
        self.news = []
        self.fields = ['title', 'link', 'summary', 'source',
                       'published', 'author']
        self.source = source

    def parse(self):
        self.entries = feedparser.parse(self.url).entries
        for entry in self.entries:
            news = News(None, None)
            if 'title' in entry:
                news.title = entry.title
            if 'link' in entry:
                news.link = entry.link
            if 'summary' in entry:
                news.content = self.markdownify(entry.summary)
            if 'published_parsed' in entry:
                news.date = mktime(entry.published_parsed)
            if 'author' in entry:
                news.author = entry.author
            news.source = self.source
            self.news.append(news)

    def get_news(self):
        return self.news

    def markdownify(self, content):
        # remove img, link
        content = bs(content, 'html.parser')
        imgs = content.find_all('img')
        for img in imgs:
            img.decompose()
        links = content.find_all('a')
        for link in links:
            link.decompose()
        content = str(content)
        return markdownify.markdownify(content)
