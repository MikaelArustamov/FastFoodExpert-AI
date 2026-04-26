import ollama
import chromadb
from ddgs import DDGS
import trafilatura
import logging
import hashlib
import socket
import requests

socket.setdefaulttimeout(10)  # not to wait long for trash URLs




logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("updater.log"),  # new file
        logging.StreamHandler()  # pasting into the console
    ]
)
logger = logging.getLogger(__name__)

# settings
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf:latest'
LANGUAGE_MODEL = 'dolphin-llama3:8b'
DB_PATH = "./potato_db"



def get_chunks(text, size=600, overlap=150):
    return [text[i:i + size] for i in range(0, len(text), size - overlap)]


def is_content_relevant(text):
    # System prompt for LLM to check the links
    check_prompt = f"""
    Analyze the following text. Ignore the .ru .cn sites
    Is it a meaningful article about French fries, potatoes, or fast food industry? 
    Or is it just technical junk, ads, or a list of languages?

    If it is a GOOD article about potatoes/fries, respond with 'VALID'.
    If it is JUNK, respond with 'TRASH'.
    Respond ONLY with one word.

    TEXT: {text[:1000]}  
    """

    response = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[{'role': 'user', 'content': check_prompt}],
        options={'temperature': 0}  # Setting minimal T for zero improvisation
    )

    verdict = response['message']['content'].strip().upper()
    return "VALID" in verdict


def run_updater():
    logger.info("Starting the knowledge update process...")


    from trafilatura.settings import use_config
    new_config = use_config()
    new_config.set("DEFAULT", "USER_AGENT",
                   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_or_create_collection(name="fries_expertise")

        queries = [
            "McDonald's french fries 2026 news -site:whatsapp.com -site:google.com -site:facebook.com",
            "fast food potato supply chain 2025 -site:://google.com",
            "Burger King fries ingredients 2024 article",
            "McDonald's fries ingredients news 2024 -site:unir.net -site:zhihu.com",
            "McDonald's french fries supply chain updates 2025 -site:facebook.com",
            "fast food news McDonald's potatoes December 2024"
        ]

        with DDGS() as ddgs:
            for q in queries:
                try:
                    logger.info(f"Searching for: {q}")
                    import time
                    time.sleep(2)

                    raw_results = ddgs.text(q, max_results=30)
                    if not raw_results:
                        continue
                except Exception as e:
                    logger.warning(f"Search failed for query '{q}': {e}")
                    continue

                for r in raw_results:
                    url = r['href'].lower()
                    forbidden = ['the-sun.com', 'thesun', 'sun.uk', 'newsweek', 'usatoday.com', 'aol.com',
                                 '://google.com']

                    if any(bad_word in url for bad_word in forbidden):
                        logger.info(f" [SHIELD] KILLING BLACKLISTED URL: {url}")
                        continue

                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    if collection.get(ids=[f"{url_hash}_0"])['ids']:
                        logger.info(f"Skipping already indexed URL: {url}")
                        continue

                    logger.info(f"Safe URL found. Downloading: {url}")

                    try:
                        import requests
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                        response = requests.get(url, headers=headers, timeout=(5, 10))
                        if response.status_code == 200:
                            downloaded = response.text
                        else:
                            logger.warning(f"Status {response.status_code} for {url}")
                            continue
                    except Exception as e:
                        logger.error(f"Time out or Connection Error on {url}: {e}")
                        continue

                    text = trafilatura.extract(downloaded)

                    if text:
                        if len(text) > 1000:
                            if is_content_relevant(text):
                                if 'check history' in text.lower() or 'world clock' in text.lower():
                                    logger.warning(f'Skipping junk technical page')
                                    continue

                        chunks = get_chunks(text)
                        logger.info(f"Processing {len(chunks)} chunks for database...")
                        for i, chunk in enumerate(chunks):

                            safe_chunk = chunk[:1500]

                            try:

                                resp = ollama.embed(model=EMBEDDING_MODEL, input=safe_chunk)
                                embed = resp['embeddings']


                                while isinstance(embed, list) and len(embed) > 0 and isinstance(embed[0], list):
                                    embed = embed[0]

                                collection.add(
                                    ids=[f"{url_hash}_{i}"],
                                    embeddings=[embed],
                                    documents=[safe_chunk],
                                    metadatas=[{'url': url, 'title': q}]
                                 )
                            except Exception as e:

                                logger.error(f"⚠Chunk {i} too big or broken, skipping: {e}")
                                continue

                        logger.info(f"Successfully added content from {url}")



    except Exception as e:
        logger.error(f"An error occurred during update: {e}", exc_info=True)


if __name__ == "__main__":
    run_updater()
    logger.info("Updater finished work.")
