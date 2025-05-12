# Importation des bibliothèques
import asyncio
import aiohttp
import feedparser
import logging
import sys

class Logger(object):
    def __init__(self, filename="console_output.txt"):
        # Redirige la sortie standard (print) vers un fichier + terminal
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")
        
    def write(self, message):
        # Écrit les messages à la fois dans le terminal et dans le fichier
        self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        # Nécessaire pour que les flux soient bien écrits immédiatement
        self.terminal.flush()
        self.log.flush()
        
# Remplace sys.stdout pour capturer tout print dans un fichier
sys.stdout = Logger()

logging.basicConfig(
    filename="error.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Configure le logging pour écrire les avertissements et erreurs dans "error.log"

def load_rss_list(filename="rss_list.txt"):
    # Lit le fichier contenant les URL des flux RSS
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]
    
def load_keywords(filename="keywords.txt"):
    # Lit le fichier contenant les mots-clés à rechercher
    with open(filename, "r") as file:
        return [line.strip() for line in file if line.strip()]
    
def find_matching_articles(parsed_feed, keywords):
    articles = []
    for entry in parsed_feed.entries:
        # Combine le titre et le résumé en minuscules
        content = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        for keyword in keywords:
            # Si un mot-clé est trouvé, l'article est ajouté à la liste
            if keyword in content:
                articles.append({
                    'title': entry.get('title', 'No title'),
                    'published': entry.get('published', 'No date'),
                    'link': entry.get('link', 'No link'),
                    'keyword': keyword
                })
                break # On évite d'ajouter le même article plusieurs fois
    return articles

async def fetch_feed(session, url):
    try:
        # Tente de récupérer le contenu du flux avec un timeout de 10 secondes
        async with session.get(url, timeout=10) as response:
            content = await response.read()
            return url, feedparser.parse(content)
    except Exception as e:
        # En cas d'erreur, enregistre un avertissement dans le fichier log
        logging.warning(f"[Erreur lors de la récupération de flux RSS] {url}: {e}")
        return url, None
    
async def scan_all_feeds(feeds_url, keywords):
    articles = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_feed(session, url) for url in feeds_url] # Prépare toutes les tâches
        for tasks in asyncio.as_completed(tasks):
            # Exécute les tâches au fur et à mesure qu'elles terminent
            url, parsed_feed = await tasks
            if parsed_feed:
                matches = find_matching_articles(parsed_feed, keywords)
                articles.extend(matches) # Ajoute les articles trouvés
    return articles
            
def display_articles(articles):
    # Affichage des articles correspondants
    print(f"\n{len(articles)} articles trouvés :\n")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"    {article['link']}")
        print(f"   Mot-clé : {article['keyword']}\n")
        
def main():
    rss_list = load_rss_list() # Charge la liste des flux RSS
    keywords = load_keywords() # Charge la liste des mots-clés
    print(f"[INFO] {len(rss_list)} flux RSS chargés.")
    print(f"[INFO] Mots-clés utilisés : {keywords}")
    
    try:
        # Lance le scan des flux de manière asynchrone
        articles = asyncio.run(scan_all_feeds(rss_list, keywords))
        display_articles(articles)
    except Exception as e:
        # Capture toute erreur non prévue
        logging.error(f"[Erreur critique] {e}")
        print("[ERREUR] Une erreur critique est survenue. Voir error.log pour plus de détails.")
   
   
# Point d’entrée du script     
if __name__ == "__main__":
    main()
    
