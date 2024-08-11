from flask import Flask, render_template, request, jsonify, session
import json
import mysql.connector
from workflow_json_schema import get_json_workflow
from workflow_schema import get_default_workflow
from get_memory import get_memory, get_chat_history
from add_to_fewshot import addToFewShot
from langchain_google_genai import ChatGoogleGenerativeAI
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from uuid import UUID


app = Flask(__name__)
app.secret_key = 'rahul rung;a'
use_personalized_schema=False

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float for numerical accuracy
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()  # Convert datetime, date, and time to ISO 8601 string format
        elif isinstance(obj, timedelta):
            return str(obj.total_seconds())  # Convert timedelta to total seconds as a string
        elif isinstance(obj, UUID):
            return str(obj)  # Convert UUID to string
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')  # Convert bytes to string (UTF-8)
        elif isinstance(obj, (set, frozenset)):
            return list(obj)  # Convert set and frozenset to list
        return super().default(obj)

app.json_encoder = CustomJSONEncoder


def load_config():
    with open("config.json", "r") as file:
        return json.load(file)

def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file)

# Check Database Connection
def check_database_connection(config):
    try:
        conn = mysql.connector.connect(
            host=config['DB_HOST'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            database=config['DB_NAME']
        )
        if conn.is_connected():
            conn.close()
            return [1, ""]
    except mysql.connector.Error as e:
        return [0, str(e)]

# Check Gemini API Connection
def check_gemini_api(google_api):
    try:
        llm = ChatGoogleGenerativeAI(google_api_key=google_api, model='gemini-pro', temperature=0.9)
        llm.invoke("Write a poem on rain water.")
        return [1, ""]
    except Exception as e:
        return [0, str(e)]

@app.route('/')
def index():
    if 'chat_sessions' not in session:
        session['chat_sessions'] = {"1": {'messages': [], 'key': 1}}
        session['current_chat'] = "1"
    if 'current_chat' not in session and session['chat_sessions']:
        session['current_chat'] = list(session['chat_sessions'].keys())[0]
    session.modified = True
    return render_template('db_details.html')

@app.route('/submit_db_details', methods=['POST'])
def submit_db_details():
    db_user = request.form.get("db_user", "")
    db_password = request.form.get("db_password", "")
    db_host = request.form.get("db_host", "")
    db_name = request.form.get("db_name", "")
    google_api = request.form.get("google_api", "")

    config = load_config()
    config.update({
        "db_user": db_user,
        "db_password": db_password,
        "db_host": db_host,
        "db_name": db_name,
        "google_api": google_api
    })
    
    db_status = check_database_connection(config)
    api_status = check_gemini_api(google_api)
    
    if db_status[0] == 0:
        return render_template('db_details.html', error_message=db_status[1])
    if api_status[0] == 0:
        return render_template('db_details.html', error_message=api_status[1])

    save_config(config)
    return render_template('index.html', chat_sessions=session['chat_sessions'])

@app.route('/update_schema', methods=['POST'])
def update_schema():
    data = request.json
    use_personalized_schema = data.get('usePersonalizedSchema', False)
    session['use_personalized_schema'] = use_personalized_schema
    session.modified = True
    return jsonify({"success": True})


@app.route('/new_chat', methods=['POST'])
def new_chat():
    chat_sessions = session.get('chat_sessions', {})
    chat_id = str(len(chat_sessions) + 1)
    chat_sessions[chat_id] = {'messages': [], 'key': 1}
    session['chat_sessions'] = chat_sessions
    session['current_chat'] = chat_id
    session.modified = True
    return jsonify({'chat_id': chat_id, 'messages': []})

@app.route('/switch_chat', methods=['POST'])
def switch_chat():
    chat_id = request.form['chat_id']
    chat_sessions = session.get('chat_sessions', {})
    if chat_id in chat_sessions:
        session['current_chat'] = chat_id
        session.modified = True
        return jsonify({'messages': chat_sessions[chat_id]['messages']})
    return jsonify({"error": "Chat session not found"}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    user_input = data.get('user_input')
    if not user_input:
        return jsonify({"error": "No user input provided"}), 400
    
    if 'current_chat' not in session:
        return jsonify({"error": "No chat session active"}), 400
    
    chat_id = str(session['current_chat'])
    chat_sessions = session.get('chat_sessions', {})
    
    if chat_id not in chat_sessions or not isinstance(chat_sessions[chat_id], dict):
        return jsonify({"error": f"Chat session {chat_id} not found"}), 400

    key = chat_sessions[chat_id].get('key', 1)

    use_personalized_schema = session.get('use_personalized_schema', False)
    if use_personalized_schema:
        app_workflow = get_json_workflow(chat_id)
    else:
        app_workflow = get_default_workflow(chat_id)

    input_dict = {'message': [user_input]}
    result = app_workflow.invoke(input_dict)

    message = {"user_input": user_input, "result": result, "key": key}
    chat_sessions[chat_id]['messages'].append(message)
    chat_sessions[chat_id]['key'] += 1
    session['chat_sessions'] = chat_sessions
    session.modified = True

    return jsonify(message)

@app.route('/update_chat_history')
def update_chat_history():
    chat_id = session.get('current_chat')
    chat_sessions = session.get('chat_sessions', {})

    if chat_id not in chat_sessions:
        return jsonify({"error": f"Chat session {chat_id} not found"}), 400

    chat_history = chat_sessions[chat_id]['messages']
    
    # Summarize chat history using ConversationSummaryBufferMemory
    memory = get_memory()
    for msg in chat_history:
        user_input = msg['user_input']
        answer = msg['result']['answer']
        memory.save_context({"user_input": user_input}, {"output": answer})

    
    summarized_history = memory.load_memory_variables({})

    chat_sessions[chat_id]['summarized_history'] = summarized_history
    session['chat_sessions'] = chat_sessions
    session.modified = True
    return jsonify({"summarized_history": summarized_history})

    

@app.route('/summary')
def summary():
    chat_id = session.get('current_chat')
    result = get_chat_history(chat_id)
    
    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)




@app.route('/update_fewshot', methods=['POST'])
def update_fewshot():
    user_query = request.form.get('user_query')
    sql_query = request.form.get('sql_query')

    if not user_query or not sql_query:
        return 'Missing user_query or sql_query', 400

    addToFewShot(user_query, sql_query)

    chat_id = session.get('current_chat')
    chat_sessions = session.get('chat_sessions', {})
    for message in chat_sessions[chat_id]['messages']:
        if message['user_input'] == user_query:
            message['result']['sql_query'] = sql_query

    session['chat_sessions'] = chat_sessions
    session.modified = True
    return '', 204

@app.route('/run_query', methods=['POST'])
def run_query():
    sql_query = request.form['sql_query']
    config = load_config()
    try:
        conn = mysql.connector.connect(
            host=config["DB_HOST"],
            user=config["DB_USER"],
            password=config["DB_PASSWORD"],
            database=config["DB_NAME"]
        )
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        conn.close()

        data = [dict(zip(column_names, row)) for row in result]
        return jsonify({"columns": column_names, "data": data})
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_sql_query', methods=['POST'])
def update_query():
    chat_id = request.form.get('chat_id')
    message_key = request.form.get('key')
    new_sql_query = request.form.get('sql_query')

    if not chat_id or not message_key or not new_sql_query:
        return jsonify({"error": "Missing chat_id, key, or sql_query"}), 400

    chat_sessions = session.get('chat_sessions', {})
    
    if chat_id not in chat_sessions:
        return jsonify({"error": f"Chat session {chat_id} not found"}), 400

    try:
        messages = chat_sessions[chat_id]['messages']
        for message in messages:
            if str(message['key']) == message_key:
                message['result']['sql_query'] = new_sql_query
                session['chat_sessions'] = chat_sessions
                session.modified = True
                return jsonify({"success": "SQL query updated successfully"}), 200

        return jsonify({"error": "Message with the specified key not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/database_details')
def database_details():
    return render_template('database_details.html')

@app.route('/save_tables', methods=['POST'])
def save_tables():
    tables = request.json
    
    # Clear the JSON file
    open('static/database_details.json', 'w').close()
    
    # Write the tables data to the JSON file
    with open('static/database_details.json', 'w') as f:
        json.dump(tables, f, indent=4)
    
    return jsonify({"message": "Tables saved successfully!"})

# Function to clear and save updated joins data
def clear_and_save_joins_data(data):
    with open('static/database_joins.json', 'w') as file:
        json.dump({"Joins": []}, file)  # Clear the file by writing an empty Joins array
    with open('static/database_joins.json', 'w') as file:
        json.dump(data, file, indent=4)  # Write the updated data

@app.route('/save_joins', methods=['POST'])
def save_joins():
    try:
        data = request.json
        clear_and_save_joins_data(data)
        return jsonify({'message': 'Joins data saved successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
