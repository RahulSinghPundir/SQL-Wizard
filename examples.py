import os
import json
from langchain_community.vectorstores import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_huggingface import HuggingFaceEmbeddings

def get_examples():
    # Get the current script directory
    script_dir = os.path.dirname("E:\\Codes\\Ai_Ml\\PWD\\GUI\\")
    # Construct the full path to the fewshot.json file
    file_path = os.path.join(script_dir, 'fewshot.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    examples = data["fewshots_examples"]
    return examples

def get_example_selector():
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        HuggingFaceEmbeddings(),
        Chroma,
        k=2,
        input_keys=["input"],
    )
    return example_selector

examples = get_examples()
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
