import ollama
import chromadb

# retrival system
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf:latest'

# Uploading dataset (leaving migrations for DB)
dataset = []
with open('FrenchFriesExpert.txt', 'r') as file:
    text_data = file.read()
    print(f'Loaded expert data')

# establishing vector database (ChromaDB)
client = chromadb.PersistentClient(path="./potato_db")
collection = client.get_or_create_collection(name="fries_expertise")

# 'clever' chunking & overlap 75
def get_chunks(text, size=300, overlap=75):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i + size])
    return chunks

# check if DB is empty
if collection.count() == 0:
    print("Database is empty. Chunking and indexing...")
    chunks = get_chunks(text_data)
    for i, chunk in enumerate(chunks):
        embed = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
        collection.add(ids=[str(i)], embeddings=[embed], documents=[chunk])
    print(f'Added {len(chunks)} smart chunks to the database')

def retrieve(query, top_n=3):
    # Generate embedding for the user query
    resp = ollama.embed(model=EMBEDDING_MODEL, input=query)
    query_emb = resp['embeddings']

    # Fix potential nested list issue
    if isinstance(query_emb, list) and len(query_emb) > 0 and isinstance(query_emb[0], list):
        query_emb = query_emb[0]

    # Query the ChromaDB collection
    results = collection.query(query_embeddings=[query_emb], n_results=top_n)

    formatted_results = []
    context_text = ""

    # Process the results
    docs = results['documents'][0]
    dist = results['distances'][0]
    meta = results['metadatas'][0]

    for i in range(len(docs)):
        chunk_text = docs[i]
        chunk_score = 1 - dist[i]
        context_text += f'\n---\n{chunk_text} '

        source_url = "No source"
        if meta[i] and 'url' in meta[i]:
            source_url = meta[i]['url']

        formatted_results.append((chunk_text, chunk_score, source_url))

    return formatted_results, context_text
