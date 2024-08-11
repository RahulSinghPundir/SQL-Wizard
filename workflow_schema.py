from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX
from examples import get_example_selector
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from get_llm import get_llm_sql
from get_memory import get_memory, get_chat_history
import json
from sqlalchemy import create_engine, inspect

memory = get_memory()
chat_history = None
llm = get_llm_sql()

file = json.load(open("config.json"))
DB_USER = file["DB_USER"]
DB_PASSWORD = file["DB_PASSWORD"]
DB_HOST = file["DB_HOST"]
DB_NAME = file["DB_NAME"]

class GraphState(TypedDict):
    message: Optional[str] = None
    classification: Optional[int] = None
    recommended_tables: Optional[str] = None
    sql_query: Optional[str] = None
    query_result: Optional[str] = None
    answer: Optional[str] = None


class States:
    @staticmethod
    def recommendTables(state):
        print("sadfffffffffffffffffffffffffffffffffffffffffffffff workflow_schema")
        user_query = state["message"][0]

        # Connect to the database and get table information
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        inspector = inspect(engine)
        table_info = {}

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            column_descriptions = ', '.join([f"{col['name']} ({col['type']})" for col in columns])
            table_info[table_name] = column_descriptions

        # Format the table information for the prompt
        table_descriptions = '\n'.join([f"Table: {table_name}\nColumns: {desc}" 
                                        for table_name, desc in table_info.items()])

        table_recommendation_prompt = PromptTemplate(
            input_variables=["user_query", "chat_history", "table_descriptions"],
            template="""
            You are an assistant that recommends relevant database tables for SQL queries.

            Return the names of ALL the SQL tables only from the given table descriptions. Do not assume any table that MIGHT be relevant to the user question.

            History: {chat_history}
            Table Descriptions: {table_descriptions}

            User input: {user_query}

            Answer only with table names in comma-separated format.
            """
        )

        recommendation_chain = LLMChain(llm=llm, prompt=table_recommendation_prompt, output_key="table_list")
        recommendations = recommendation_chain.run({
            "user_query": user_query,
            "chat_history": chat_history,
            "table_descriptions": table_descriptions
        }).strip()

        recommended_tables = [name.strip() for name in recommendations.split(',')]
        state["recommended_tables"] = recommended_tables
        return state

    @staticmethod
    def generateSqlQuery(state):
        try:
            history=chat_history['chat_history']
        except Exception as e:
            history=chat_history
        print(history)
        user_input = state["message"][0]
        recommended_tables = state["recommended_tables"]
        sql_database = SQLDatabase.from_uri(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}", include_tables=recommended_tables, sample_rows_in_table_info=5)
        sql_query_prefix = f"""
            You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
            Unless the user specifies in the question a specific number of examples to obtain, query for at most 5 results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
            Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
            Use CURDATE() function to get the current date, if the question involves "today".

            history: {history}
            Use the following format:
            SQLQuery: SQL Query to run and include ;
            SQLResult: Result of the SQLQuery
            Answer: Final answer here
            """
        example_prompt = PromptTemplate(
            input_variables=["input", "query"],
            template="Question: {input}\nQuery: {query}",
        )

        example_selector = get_example_selector()

        query_prompt_template = FewShotPromptTemplate(
            example_selector=example_selector,
            example_prompt=example_prompt,
            prefix=sql_query_prefix,
            suffix=PROMPT_SUFFIX + "SQL Query.",
            input_variables=["input", "top_k"],
        )

        sql_chain = SQLDatabaseChain.from_llm(llm, sql_database, prompt=query_prompt_template, verbose=True, return_sql=True, use_query_checker=False)
        sql_execution_result = sql_chain.invoke(user_input)
        sql_query = sql_execution_result["result"]
        sql_query = sql_query[sql_query.find("SELECT"):sql_query.find(";")]
        state["sql_query"] = sql_query
        return state

    @staticmethod
    def executeSqlQuery(state):
        recommended_tables = state["recommended_tables"]
        sql_query = state["sql_query"]
        sql_database = SQLDatabase.from_uri(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}", include_tables=recommended_tables, sample_rows_in_table_info=5)
        query_results = SQLDatabase.run(sql_database, sql_query)
        state["query_result"] = query_results
        return state

    @staticmethod
    def generateAnswer(state):
        user_input = state["message"][0]
        sql_query = state["query_result"]
        query_result = state["query_result"] or "No result."

        answer_template = """Rephrase the answer, {query_result}, to the question, {user_input}, based on the SQL query, {sql_query}, in a single sentence."""
        answer_prompt = PromptTemplate(input_variables=["query_result", "user_input", "sql_query"], template=answer_template)
        chat_chain = LLMChain(llm=llm, prompt=answer_prompt, memory=memory)
        answer = chat_chain.run({"user_input": user_input, "sql_query": sql_query, "query_result": query_result})
        state["answer"] = answer
        return state

def get_default_workflow(chat_id):
    global chat_history
    chat_history = get_chat_history(chat_id)['chat_history']


    workflow = StateGraph(GraphState)

    workflow.add_node("recommend_tables", States.recommendTables)
    workflow.add_node("generate_sql_query", States.generateSqlQuery)
    workflow.add_node("execute_sql_query", States.executeSqlQuery)
    workflow.add_node("generate_answer", States.generateAnswer)

    workflow.add_edge("recommend_tables", "generate_sql_query")
    workflow.add_edge("generate_sql_query", "execute_sql_query")
    workflow.add_edge("execute_sql_query", "generate_answer")
    workflow.add_edge("generate_answer", END)

    workflow.set_entry_point("recommend_tables")
    return workflow.compile()