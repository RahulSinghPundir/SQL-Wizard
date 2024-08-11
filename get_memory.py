from langchain.memory import ConversationSummaryBufferMemory
from get_llm import get_llm_summary
import json
from flask import session

def get_memory():
    
    # Set up and return the memory object.
    file=json.load(open("config.json"))
    memory = ConversationSummaryBufferMemory(
            memory_key="chat_history",
            input_key="user_input",
            llm=get_llm_summary(),
            max_token_limit=file["MAX_TOKEN_LIMIT"]
        )
    return memory

def get_chat_history(chat_id):
    chat_sessions = session.get('chat_sessions', {})
    
    if not chat_id or chat_id not in chat_sessions:
        return {"error": "Chat session not found"}
    
    summarized_history = chat_sessions.get(chat_id, {}).get('summarized_history', '')

    return {"chat_history": summarized_history}