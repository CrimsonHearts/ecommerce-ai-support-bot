#!/usr/bin/env python3
"""
E-Commerce AI Support Bot - Web Version
Supports OpenAI, Kimi (Moonshot), or local models
"""

import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string
from orders_db import lookup_order, get_status_message

app = Flask(__name__)

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()  # openai, kimi, or local
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
LOCAL_API_URL = os.getenv("LOCAL_API_URL", "http://localhost:11434/v1/chat/completions")

# WhatsApp Configuration
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
WHATSAPP_WHITELIST = os.getenv("WHATSAPP_WHITELIST", "").split(",")  # Comma-separated phone numbers
WHATSAPP_WHITELIST = [num.strip() for num in WHATSAPP_WHITELIST if num.strip()]  # Clean up
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")  # For WhatsApp Business API or third-party service

# In-memory session storage for WhatsApp conversations
whatsapp_sessions = {}

SYSTEM_PROMPT = """You are a helpful, friendly customer support bot for an e-commerce store called TechGear.
Your job is to help customers check their order status.

Guidelines:
- Be warm and professional
- Ask for order ID or email if not provided
- Keep responses concise but complete
- If order not found, ask them to double-check the info
- Offer to connect to human support for complex issues"""


def get_ai_response(messages):
    """Get response from configured AI provider."""
    
    if AI_PROVIDER == "kimi" and KIMI_API_KEY:
        # Kimi/Moonshot API
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 200
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    elif AI_PROVIDER == "local":
        # Local model (Ollama, etc.)
        response = requests.post(
            LOCAL_API_URL,
            json={
                "model": os.getenv("LOCAL_MODEL", "llama2"),
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        # Handle different local API formats
        if "message" in data:
            return data["message"]["content"]
        elif "choices" in data:
            return data["choices"][0]["message"]["content"]
        return str(data)
    
    else:
        # Default: OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content


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
    
    # Build messages
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
        bot_response = get_ai_response(messages)
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
    return jsonify({'status': 'healthy', 'provider': AI_PROVIDER})


# WhatsApp Webhook Endpoints
@app.route('/whatsapp/webhook', methods=['GET'])
def whatsapp_verify():
    """Verify webhook for WhatsApp Business API."""
    # Meta/WhatsApp verification
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == verify_token:
        return challenge, 200
    return 'Verification failed', 403


@app.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """Receive WhatsApp messages."""
    if not WHATSAPP_ENABLED:
        return jsonify({'status': 'WhatsApp not enabled'}), 400
    
    data = request.json
    
    try:
        # Extract message data (Meta/WhatsApp Business API format)
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            return jsonify({'status': 'No messages'}), 200
        
        message = messages[0]
        phone_number = message.get('from')  # Sender's phone number
        message_text = message.get('text', {}).get('body', '')
        
        # Check whitelist
        if WHATSAPP_WHITELIST and phone_number not in WHATSAPP_WHITELIST:
            send_whatsapp_message(phone_number, "Sorry, you're not authorized to use this service.")
            return jsonify({'status': 'Unauthorized'}), 403
        
        # Get or create session
        if phone_number not in whatsapp_sessions:
            whatsapp_sessions[phone_number] = []
        
        conversation = whatsapp_sessions[phone_number]
        
        # Build messages for AI
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_for_ai.extend(conversation)
        messages_for_ai.append({"role": "user", "content": message_text})
        
        # Extract potential order info
        potential_query = None
        words = message_text.split()
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
                messages_for_ai.append({"role": "system", "content": f"[Order found: {order_info['order_id']}. {status_msg}]"})
            else:
                messages_for_ai.append({"role": "system", "content": f"[No order found for: {potential_query}]"})
        
        # Get AI response
        try:
            bot_response = get_ai_response(messages_for_ai)
        except Exception as e:
            bot_response = "I'm having trouble right now. Please try again later."
        
        # Update session
        conversation.append({"role": "user", "content": message_text})
        conversation.append({"role": "assistant", "content": bot_response})
        
        # Keep history manageable
        if len(conversation) > 20:
            conversation = conversation[-20:]
        
        # Send response back via WhatsApp
        send_whatsapp_message(phone_number, bot_response)
        
        return jsonify({'status': 'Message processed'}), 200
        
    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 500


def send_whatsapp_message(phone_number, message):
    """Send message via WhatsApp Business API or third-party service."""
    # This uses Meta's WhatsApp Business API
    # You'll need to set up a WhatsApp Business account and get access token
    
    business_phone_id = os.getenv("WHATSAPP_BUSINESS_PHONE_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    if not business_phone_id or not access_token:
        print(f"[WhatsApp not configured] To {phone_number}: {message}")
        return
    
    url = f"https://graph.facebook.com/v18.0/{business_phone_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")


@app.route('/whatsapp/send', methods=['POST'])
def whatsapp_send_manual():
    """Manual endpoint to send WhatsApp message (for testing)."""
    if not WHATSAPP_ENABLED:
        return jsonify({'error': 'WhatsApp not enabled'}), 400
    
    data = request.json
    phone_number = data.get('phone')
    message = data.get('message')
    
    if not phone_number or not message:
        return jsonify({'error': 'Phone and message required'}), 400
    
    # Check whitelist
    if WHATSAPP_WHITELIST and phone_number not in WHATSAPP_WHITELIST:
        return jsonify({'error': 'Phone number not whitelisted'}), 403
    
    send_whatsapp_message(phone_number, message)
    return jsonify({'status': 'Message sent'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
