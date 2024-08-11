function generateTableHTML(columns, data) {
    let tableHTML = '<table><thead><tr>';
    columns.forEach(column => {
        tableHTML += `<th>${column}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    data.forEach(row => {
        tableHTML += '<tr>';
        columns.forEach(column => {
            tableHTML += `<td>${row[column]}</td>`;
        });
        tableHTML += '</tr>';
    });
    tableHTML += '</tbody></table>';
    return tableHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const summaryButton = document.getElementById('summary-button');
    const summaryModal = document.getElementById('summary-modal');
    const closeButton = document.querySelector('.close-button');
    const summaryText = document.getElementById('summary-text');
    const fileNameInput = document.getElementById('file-name');
    const fileContentInput = document.getElementById('file-content');
    const newChatButton = document.getElementById('new-chat-button');
    const chatList = document.getElementById('chat-list');
    const showDatabaseButton = document.getElementById('show-database-button');
    const personalizeToggle = document.getElementById('personalize-toggle');
    let isPersonalized=false;

        
    showDatabaseButton.onclick = () => {
        window.open('/database_details');
    };
    

    
    sendButton.addEventListener('click', () => {
        const userInputValue = userInput.value;
        if (userInputValue.trim()) {
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_input: userInputValue })
            })
            .then(response => response.json())
            .then(message => {
                const userMessage = document.createElement('div');
                userMessage.classList.add('chat-message', 'user-message');
                userMessage.setAttribute("data-key", message.key);
                userMessage.setAttribute("data-chat-id", message.chat_id);
                userMessage.innerHTML = `<p class="user-input">${message.user_input}</p>`;
                chatContainer.appendChild(userMessage);
    
                const assistantMessage = document.createElement('div');
                assistantMessage.classList.add('chat-message', 'assistant-message');
                assistantMessage.setAttribute("data-key", message.key);
                assistantMessage.setAttribute("data-chat-id", message.chat_id);
                assistantMessage.innerHTML = `
                    <p>${message.result.answer}</p>
                    <textarea class="sql-query" data-key="${message.key}" data-chat-id="${message.chat_id}">${message.result.sql_query}</textarea>
                    <button class="add-fewshot-button" data-key="${message.key}" data-chat-id="${message.chat_id}">Add to Training Data</button>
                    <button class="run-button" data-key="${message.key}" data-chat-id="${message.chat_id}">Run Query</button>
                    <div class="query-result-container" style="max-height: 200px; overflow-y: auto; margin:2px;"></div>
                    <button class="open-window-button" data-key="${message.key}" data-chat-id="${message.chat_id}">Open in Separate Window</button>`;
                chatContainer.appendChild(assistantMessage);
    
                userInput.value = '';
            })
            .then(() => {
                fetch('/update_chat_history')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        console.log("Chat history updated.")
                    }
                })
                .catch(error => console.error('Error:', error));
            });
        }
    });
    

    newChatButton.addEventListener('click', () => {
        fetch('/new_chat', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            const newChatItem = document.createElement('li');
            newChatItem.setAttribute('data-chat-id', data.chat_id);
            newChatItem.textContent = 'New Chat';
            chatList.appendChild(newChatItem);

            newChatItem.addEventListener('click', () => {
                switchChatSession(data.chat_id);
            });

            // Clear the chat container
            chatContainer.innerHTML = '';
        });
    });

    const switchChatSession = (chat_id) => {
        fetch('/switch_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ chat_id })
        })
        .then(response => response.json())
        .then(data => {
            chatContainer.innerHTML = '';
            data.messages.forEach(message => {
                const userMessage = document.createElement('div');
                userMessage.classList.add('chat-message', 'user-message');
                userMessage.setAttribute("data-key", message.key);
                userMessage.setAttribute("data-chat-id", chat_id);
                userMessage.innerHTML = `<p>${message.user_input}</p>`;
                chatContainer.appendChild(userMessage);

                const assistantMessage = document.createElement('div');
                assistantMessage.classList.add('chat-message', 'assistant-message');
                assistantMessage.setAttribute("data-key", message.key);
                assistantMessage.setAttribute("data-chat-id", chat_id);
                assistantMessage.innerHTML = `
                    <p>${message.result.answer}</p>
                    <textarea class="sql-query" data-key="${message.key}" data-chat-id="${chat_id}">${message.result.sql_query}</textarea>
                    <button class="add-fewshot-button" data-key="${message.key}" data-chat-id="${chat_id}">Add to Training Data</button>
                    <button class="run-button" data-key="${message.key}" data-chat-id="${chat_id}">Run Query</button>
                    <div class="query-result-container" style="max-height: 200px; overflow-y: auto;margin:2px;"></div>
                    <button class="open-window-button" data-key="${message.key}" data-chat-id="${chat_id}">Open in Separate Window</button>`;
                chatContainer.appendChild(assistantMessage);
            });
        });
    };

    chatList.addEventListener('click', (event) => {
        const chatId = event.target.getAttribute('data-chat-id');
        if (chatId) {
            switchChatSession(chatId);
        }
    });

    summaryButton.addEventListener('click', () => {
        fetch('/summary')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const chatHistoryText = data.chat_history.chat_history || 'No chat history available';
                    summaryText.textContent = chatHistoryText;
                    summaryModal.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error fetching summary:', error);
                alert('An error occurred while fetching the summary.');
            });
    });
    
    
    

    closeButton.addEventListener('click', () => {
        summaryModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == summaryModal) {
            summaryModal.style.display = 'none';
        }
    });


    personalizeToggle.addEventListener('change', function() {
        isPersonalized = this.checked;
        console.log(isPersonalized);
        fetch('/update_schema', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ usePersonalizedSchema: isPersonalized })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Schema updated successfully');
            } else {
                console.error('Error updating schema:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    document.addEventListener('click', (event) => {
        const key = event.target.getAttribute('data-key');
        const chatId = event.target.getAttribute('data-chat-id');
        if (!key || !chatId) return; // exit if key or chat_id is null

        if (event.target.classList.contains('add-fewshot-button')) {
            const userQuery = document.querySelector(`.chat-message[data-key="${key}"][data-chat-id="${chatId}"] p`).innerHTML;
            const sqlQuery = document.querySelector(`.assistant-message[data-key="${key}"][data-chat-id="${chatId}"] .sql-query`).value;
            fetch('/update_fewshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ user_query: userQuery, sql_query: sqlQuery })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                alert('Query add-fewshotd successfully');
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        }

        if (event.target.classList.contains('run-button')) {
            const sqlQuery = document.querySelector(`.assistant-message[data-key="${key}"][data-chat-id="${chatId}"] .sql-query`).value;
            const queryResultContainer = document.querySelector(`.assistant-message[data-key="${key}"][data-chat-id="${chatId}"] .query-result-container`);
            fetch('/run_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ sql_query: sqlQuery })
            })
            .then(response => response.json())
            .then(result => {
                if (result.data && result.data.length > 0) {
                    const tableHTML = generateTableHTML(result.columns, result.data);
                    queryResultContainer.innerHTML = tableHTML;
                } else {
                    queryResultContainer.textContent = 'No results found.';
                }
            });
        }

        if (event.target.classList.contains('open-window-button')) {
            const sqlQuery = document.querySelector(`.assistant-message[data-key="${key}"][data-chat-id="${chatId}"] .sql-query`).value;
            fetch('/run_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ sql_query: sqlQuery })
            })
            .then(response => response.json())
            .then(result => {
                const resultWindow = window.open("", "Result Window", "width=600,height=400");
                console.log(result)
                if (result.data && result.data.length > 0) {
                    const tableHTML = generateTableHTML(result.columns, result.data);
                    resultWindow.document.write('<html><body>' + tableHTML + '</body></html>');
                } else {
                    resultWindow.document.write('<html><body>No results found.</body></html>');
                }
            });
        }
    });

    document.addEventListener('input', (event) => {
        if (event.target.classList.contains('sql-query')) {
            const key = event.target.getAttribute('data-key');
            const chatId = event.target.getAttribute('data-chat-id');
            const updatedQuery = event.target.value;
    
            fetch('/update_sql_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ key, chat_id: chatId, sql_query: updatedQuery })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.error || 'Network response was not ok');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log('SQL query updated successfully');
                } else if (data.error) {
                    console.error('Error:', data.error);
                }
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
        }
    });
    
});
