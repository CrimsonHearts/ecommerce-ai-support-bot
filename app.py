#!/usr/bin/env python3
"""
E-Commerce AI Support Bot - Web Version
Deployed on Render (or any Flask host)
"""

import os
import json
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
from orders_db import lookup_order, get_status_message

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful, friendly customer support bot for an e-commerce store called TechGear.
Your job is to help customers check their order status.

Guidelines:
- Be warm and professional
- Ask for order ID or email if not provided
- Keep responses concise but complete
- If order not found, ask them to double-check the info
- Offer to connect to human support for complex issues"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TechGear AI Support</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .chat-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 500px;
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-header h1 { font-size: 1.5rem; margin-bottom: 5px; }
        .chat-header p { opacity: 0.9; font-size: 0.9rem; }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.4;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        .message.bot {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .chat-input {
            display: flex;
            padding: 15px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            border-color: #667eea;
        }
        .chat-input button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            margin-left: 10px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }
        .chat-input button:hover {
            background: #5a6fd6;
        }
        .typing {
            font-style: italic;
            color: #888;
            padding: 10px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🛒 TechGear Support</h1>
            <p>AI-powered order assistance</p>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message bot">Hello! Welcome to TechGear support. I can help you check your order status. What can I assist you with today?</div>
        </div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Type your message..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let conversation = [];
        
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'bot');
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function showTyping() {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'typing';
            div.id = 'typing';
            div.textContent = 'Bot is typing...';
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            input.value = '';
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, history: conversation})
                });
                const data = await response.json();
                hideTyping();
                addMessage(data.response, false);
                conversation = data.history;
            } catch (error) {
                hideTyping();
                addMessage('Sorry, I\'m having trouble connecting. Please try again.', false);
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    """Serve the chat interface."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    data = request.json
    user_message = data.get('message', '')
    conversation = data.get('history', [])
    
    # Build messages for OpenAI
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})
    
    # Extract potential order info
    potential_query = None
    words = user_message.split()
    for word in words:
        if word.upper().startswith("ORD-") or word.startswith("#") or word.isdigit():
            potential_query = word.replace("#", "")
            break
        if "@" in word:
            potential_query = word
            break
    
    # Look up order if found
    if potential_query:
        order_info = lookup_order(potential_query)
        if order_info.get("found"):
            status_msg = get_status_message(order_info)
            messages.append({"role": "system", "content": f"[Order found: {order_info['order_id']}. {status_msg}]"})
        else:
            messages.append({"role": "system", "content": f"[No order found for: {potential_query}]"})
    
    # Get AI response
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        bot_response = f"I'm having trouble right now. Please try again later."
    
    # Update conversation history
    conversation.append({"role": "user", "content": user_message})
    conversation.append({"role": "assistant", "content": bot_response})
    
    # Keep history manageable
    if len(conversation) > 20:
        conversation = conversation[-20:]
    
    return jsonify({
        'response': bot_response,
        'history': conversation
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
