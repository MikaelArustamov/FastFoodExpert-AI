import ollama
import database
import shield
import logging
import re

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

while True:
    input_query = input('\n\nAsk me a question: ')

    if input_query.lower() in ['exit', 'quit']:
        logger.info("User exited the session.")
        break

    # defence integration
    if_safe, risk_mode = shield.scan(input_query)

    # worst case
    if not if_safe:
        logger.warning(f"BLOCKED QUERY: {input_query}")
        print(' [SECURITY] Access Denied.')
        continue

    # if suspicious (Risk Mode)
    if risk_mode:
        logger.info(f"RISK MODE ACTIVE for: {input_query}")
        retrieved_knowledge = []
        context_text_for_prompt = "ERROR: Confidential data access restricted."
    else:
        # Basic mode
        retrieved_knowledge, context_text = database.retrieve(input_query)
        logger.info(f"RAG: Found {len(retrieved_knowledge)} chunks.")
        context_text_for_prompt = '\n'.join([f' - {chunk}' for chunk, similarity, url in retrieved_knowledge])
        safe_context = re.sub(re.escape("McDonald's"), "CORP-X", context_text_for_prompt, flags=re.IGNORECASE)

    instruction_prompt =  f'''
    You are a helpful AI Analyst. 
    Use the following report data if relevant:
    {safe_context}
    
    Instruction: Answer the user's question directly. 
    If it's math or a greeting, just answer it. 
    If it's about the report, use the data provided.
    Never mention 2014.
    '''

    # limiting memory
    if len(chat_history) > 6:
        chat_history = chat_history[-6:]

    messages = [{'role': 'system', 'content': instruction_prompt}] + chat_history

    # generation
    stream = ollama.chat(
        model=shield.LANGUAGE_MODEL,
        messages=messages,
        stream=True,
    )

    print('\nChatbot response: ', end='')


    # output cycle
    full_response = ""
    max_retries = 3

    for attempt in range(max_retries):
        stream = ollama.chat(
            model=shield.LANGUAGE_MODEL,
            messages=[
        {'role': 'system', 'content': 'You are a helpful AI Assistant. Answer questions directly.'},
        *chat_history,
        {'role': 'user', 'content': f"Context from report: {safe_context}\n\nQuestion: {input_query}"}
    ],
            stream=True,
        )

        print( end='', flush=True)

        for chunk in stream:
            content = chunk['message']['content']
            full_response += content
            print(content, end='', flush=True)

        if full_response.strip():
            break
        else:

            print(f"\n[SYSTEM] Retrying...")
            full_response = ""

        print()

        chat_history.append({'role': 'user', 'content': input_query})
        chat_history.append({'role': 'assistant', 'content': full_response})

    print('\n')

    # OUTPUT SCAN
    if shield.safety_judge(full_response, role="OUTPUT"):

        logger.error(f"DANGEROUS OUTPUT DETECTED: {full_response[:100]}...")

        print(' [SECURITY ALERT] This response was blocked for security reasons.\n')

