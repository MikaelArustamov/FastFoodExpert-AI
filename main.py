import ollama
import database
import shield
import logging
import re
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel



logging.getLogger().handlers = [logging.FileHandler("chat.log", encoding='utf-8')]

logging.getLogger().setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("chat.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# setting level WARNING for security
logging.getLogger('httpx').setLevel(logging.WARNING)

chat_history = []  # we will track the point of the talk (last 6 msgs)



app = FastAPI(title="PotatoExpert API")


chat_history = []



class UserQuery(BaseModel):
    text: str


@app.post("/ask")
async def ask_expert(query_data: UserQuery):
    global chat_history
    input_query = query_data.text

    # 1. DEFENCE INTEGRATION (Shield)
    if_safe, risk_mode = shield.scan(input_query)

    if not if_safe:
        logger.warning(f"BLOCKED QUERY: {input_query}")
        return {"response": "[SECURITY] Access Denied.", "status": "blocked"}

    # 2. RAG LOGIC
    if risk_mode:
        logger.info(f"RISK MODE ACTIVE for: {input_query}")
        safe_context = "ERROR: Confidential data access restricted."
    else:
        # sync DB in different flow
        loop = asyncio.get_event_loop()
        retrieved_knowledge, _ = await loop.run_in_executor(None, database.retrieve, input_query)

        logger.info(f"RAG: Found {len(retrieved_knowledge)} chunks.")
        context_text_for_prompt = '\n'.join([f' - {chunk}' for chunk, _, _ in retrieved_knowledge])
        safe_context = re.sub(re.escape("McDonald's"), "CORP-X", context_text_for_prompt, flags=re.IGNORECASE)

    # 3. MEMORY LIMITING
    if len(chat_history) > 6:
        chat_history = chat_history[-6:]

    # 4. GENERATION WITH RETRIES
    full_response = ""
    max_retries = 3
    client = ollama.AsyncClient()  # Используем асинхронный клиент

    for attempt in range(max_retries):
        try:

            messages = [
                {'role': 'system', 'content': 'You are a helpful AI Assistant. Answer questions directly.'},
                *chat_history,
                {'role': 'user', 'content': f"Context from report: {safe_context}\n\nQuestion: {input_query}"}
            ]

            response = await client.chat(model=shield.LANGUAGE_MODEL, messages=messages)
            full_response = response['message']['content']

            if full_response.strip():
                break
            else:
                logger.warning(f"Empty response, retry {attempt + 1}")
        except Exception as e:
            logger.error(f"Generation error: {e}")

    # 5. OUTPUT SCAN
    if shield.safety_judge(full_response, role="OUTPUT"):
        logger.error(f"DANGEROUS OUTPUT DETECTED: {full_response[:100]}...")
        return {"response": "[SECURITY ALERT] This response was blocked.", "status": "flagged"}

    # 6. UPDATE HISTORY
    chat_history.append({'role': 'user', 'content': input_query})
    chat_history.append({'role': 'assistant', 'content': full_response})

    return {"response": full_response, "status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
