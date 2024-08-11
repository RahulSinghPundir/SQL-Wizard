import pandas as pd
import json
from sentence_transformers import SentenceTransformer

# Functianal Tools implement function which helps in getting table details 
class FunctionalTools():
    @staticmethod
    def getDatabaseDetails():
        # Load table descriptions from a CSV file
        description_df = pd.read_csv("database_table_descriptions.csv")
        description_text = ""
        for _, row in description_df.iterrows():
            description_text += f"Table Name: {row['Table']}\nTable Description: {row['Description']}\n\n"
        return description_text

    @staticmethod
    def getTableDetails(recommended_tables):
        description_text = ""
        description_df = pd.read_csv("database_table_descriptions.csv")
        description_df[description_df["Table"]=="aes"]["Table"]
        for i in recommended_tables:
            description_text+=f"Table Name: {description_df[description_df['Table']==i]['Table']}\nTable Description: {description_df[description_df['Table']==i]['Description']}\n\n"
        return description_text
    
    @staticmethod
    def getDatabaseDetailsJson():
        # Load the large JSON file
        with open('static\database_details.json', 'r') as file:
            data = json.load(file)

        # Initialize the model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        def vectorize_table(table):
            table_desc = f"{table['name']}: {table['description']}. Columns: " + ", ".join(
                [f"{col['name']} ({col['type']})" for col in table['columns']]
            )
            # print(table_desc)
            return model.encode(table_desc)

        # Vectorize the table details
        table_vectors = {table['name']: vectorize_table(table) for table in data['Tables']}

        def create_prompt(tables):
            prompt = "Here are the table relationships:\n\n"
            for table, vector in tables.items():
                prompt += f"Table: {table}\nDetails: {vector.tolist()}\n\n"
            return prompt

        # Assuming the API can handle limited text length, divide the prompts
        table_names = list(table_vectors.keys())
        chunk_size = 5  # Adjust based on API limits
        prompts = [create_prompt({name: table_vectors[name] for name in table_names[i:i + chunk_size]}) 
                for i in range(0, len(table_names), chunk_size)]

        return prompts
    
    @staticmethod
    def getTableDetailsJson(recommended_tables):
        # Load the large JSON file
        with open('static\database_details.json', 'r') as file:
            data = json.load(file)

        # Initialize the model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        def vectorize_table(table):
            table_desc = f"{table['name']}: {table['description']}. Columns: " + ", ".join(
                [f"{col['name']} ({col['type']})" for col in table['columns']]
            )
            # print(table_desc)
            return model.encode(table_desc)

        # Vectorize the table details
        table_vectors = {table['name']: vectorize_table(table) for table in data['Tables'] if (table in recommended_tables)}

        def create_prompt(tables):
            prompt = "Here are the table relationships:\n\n"
            for table, vector in tables.items():
                prompt += f"Table: {table}\nDetails: {vector.tolist()}\n\n"
            return prompt

        # Assuming the API can handle limited text length, divide the prompts
        table_names = list(table_vectors.keys())
        chunk_size = 5  # Adjust based on API limits
        prompts = [create_prompt({name: table_vectors[name] for name in table_names[i:i + chunk_size]}) 
                for i in range(0, len(table_names), chunk_size)]

        return prompts
    
    @staticmethod
    def getDatabaseJoins():
        with open('static\database_joins.json', 'r') as file:
            tables_data = json.load(file)

        # Initialize the sentence-transformers model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Vectorize the table details
        table_vectors = {}
        for table in tables_data["Joins"]:
            table_name = table["name"]
            table_desc = f"{table_name}: {table['joinType']} with {table['models']} based on {table['condition']}"
            # print(table_desc)
            table_vectors[table_name] = model.encode(table_desc)

        # Create a prompt for the Gemini API
        prompt = "Here are the table relationships:\n\n"
        for table, vector in table_vectors.items():
            prompt += f"Table: {table}\nDetails: {vector.tolist()}\n\n"

        return prompt
    
    @staticmethod
    def getTablesJoins(recommended_tables):
        with open('static\database_joins.json', 'r') as file:
            tables_data = json.load(file)

        # Initialize the sentence-transformers model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Vectorize the table details
        table_vectors = {}
        for table in tables_data["Joins"]:
            table_name = table["name"]
            if(table_name not in recommended_tables):
                continue
            table_desc = f"{table_name}: {table['joinType']} with {table['models']} based on {table['condition']}"
            # print(table_desc)
            table_vectors[table_name] = model.encode(table_desc)

        # Create a prompt for the Gemini API
        prompt = "Here are the table relationships:\n\n"
        for table, vector in table_vectors.items():
            prompt += f"Table: {table}\nDetails: {vector.tolist()}\n\n"

        return prompt