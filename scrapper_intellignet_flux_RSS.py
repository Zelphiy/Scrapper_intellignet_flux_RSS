import asyncio
import aiohttp
import feedparser
import logging
import sys

class Logger(object):
    def __init__(self, filename="console_output.txt"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")
        
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()
        
sys.stdout = Logger()

logging.basicConfig(
    filename="error.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_rss_list(filename="rss_list.txt"):
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]
    
def load_keywords(filename="keywords.txt"):
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]
    
def find_matching_articles(parsed_feed, keywords):
    articles = []
    for entry in parsed_feed.entries:
        content = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        for keyword in keywords:
            if keyword in content:
                articles.append({
                    'title': entry.get('title', 'No title'),
                    'published': entry.get('published', 'No date'),
                    'link': entry.get('link', 'No link'),
                    'keyword': keyword
                })
                break
    return articles

async def fetch_feed(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            content = await response.read()
            return url, feedparser.parse(content)
    except Exception as e:
        logging.warning(f"[Erreur lors de la récupération de flux RSS] {url}: {e}")
        return url, None
    
async def scan_all_feeds(feeds_url, keywords):
    articles = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_feed(session, url) for url in feeds_url]
        for tasks in asyncio.as_completed(tasks):
            url, parsed_feed = await tasks
            if parsed_feed:
                matches = find_matching_articles(parsed_feed, keywords)
                articles.extend(matches)
    return articles
            
def display_articles(articles):
    print(f"\n✅ {len(articles)} articles trouvés :\n")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   ➤ {article['link']}")
        print(f"   🗝️ Mot-clé : {article['keyword']}\n")
        
def main():
    rss_list = load_rss_list()
    keywords = load_keywords()
    print(f"[INFO] {len(rss_list)} flux RSS chargés.")
    print(f"[INFO] Mots-clés utilisés : {keywords}")
    
    try:
        articles = asyncio.run(scan_all_feeds(rss_list, keywords))
        display_articles(articles)
    except Exception as e:
        logging.error(f"[Erreur critique] {e}")
        print("[ERREUR] Une erreur critique est survenue. Voir error.log pour plus de détails.")
        
if __name__ == "__main__":
    main()
    
