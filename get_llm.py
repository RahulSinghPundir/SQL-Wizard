from langchain_google_genai import ChatGoogleGenerativeAI
import json
def get_llm_summary():
    """Initialize and return the summary LLM."""
    file=json.load(open("config.json"))
    return ChatGoogleGenerativeAI(
        model=file["MODEL_NAME_SUMMARY"],
        temperature=file["TEMPERATURE_SUMMARY"],
        convert_system_message_to_human=False,
        google_api_key=file["GOOGLE_API_KEY"]
    )

def get_llm_sql():
    """Initialize and return the SQL LLM."""
    file=json.load(open("config.json"))
    return ChatGoogleGenerativeAI(
        model=file["MODEL_NAME_SQL"],
        temperature=file["TEMPERATURE_SQL"],
        convert_system_message_to_human=False,
        google_api_key=file["GOOGLE_API_KEY"]
    )