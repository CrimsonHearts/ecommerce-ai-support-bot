#!/usr/bin/env python3
"""
AI Customer Support Bot for E-Commerce
Demo: Order status lookup with natural language
"""

import os
import sys
from openai import OpenAI
from orders_db import lookup_order, get_status_message

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful, friendly customer support bot for an e-commerce store called TechGear.
Your job is to help customers check their order status.

Guidelines:
- Be warm and professional
- Ask for order ID or email if not provided
- Use the lookup_order function to find orders
- Keep responses concise but complete
- If order not found, ask them to double-check the info
- Offer to connect to human support for complex issues

Current date: March 2024"""


def chat_with_bot(user_message: str, conversation_history: list = None) -> str:
    """Process user message and return bot response."""
    
    if conversation_history is None:
        conversation_history = []
    
    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    # Check if user provided order info we can look up
    # Simple extraction: look for patterns that might be order IDs or emails
    potential_query = None
    words = user_message.split()
    
    for word in words:
        # Order ID patterns: ORD-XXXX, #XXXX, just numbers
        if word.upper().startswith("ORD-") or word.startswith("#") or word.isdigit():
            potential_query = word.replace("#", "")
            break
        # Email pattern
        if "@" in word:
            potential_query = word
            break
    
    # If we found something to look up, do it
    order_info = None
    if potential_query:
        order_info = lookup_order(potential_query)
    
    # Add order info to context if found
    if order_info and order_info.get("found"):
        status_msg = get_status_message(order_info)
        context = f"\n[INTERNAL: Found order {order_info['order_id']}. {status_msg}]"
        messages.append({"role": "system", "content": context})
    elif potential_query:
        messages.append({"role": "system", "content": "\n[INTERNAL: No order found for query: " + potential_query + "]"})
    
    # Get response from AI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting right now. Error: {str(e)}"


def run_demo():
    """Interactive demo of the support bot."""
    print("=" * 60)
    print("🛒 TechGear AI Support Bot Demo")
    print("=" * 60)
    print("\nSample orders you can ask about:")
    print("  • Order ID: ORD-2024-001 (delivered)")
    print("  • Order ID: ORD-2024-002 (shipped)")
    print("  • Order ID: ORD-2024-003 (processing)")
    print("  • Order ID: ORD-2024-004 (out for delivery)")
    print("  • Or use emails: sarah@example.com, mike@example.com, etc.")
    print("\nType 'quit' to exit\n")
    
    conversation = []
    
    # Initial greeting
    greeting = "Hello! Welcome to TechGear support. I can help you check your order status. What can I assist you with today?"
    print(f"🤖 Bot: {greeting}\n")
    conversation.append({"role": "assistant", "content": greeting})
    
    while True:
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n🤖 Bot: Thanks for chatting! Have a great day!")
            break
        
        if not user_input:
            continue
        
        conversation.append({"role": "user", "content": user_input})
        
        response = chat_with_bot(user_input, conversation[:-1])
        print(f"\n🤖 Bot: {response}\n")
        
        conversation.append({"role": "assistant", "content": response})
        
        # Keep conversation manageable
        if len(conversation) > 10:
            conversation = conversation[-10:]


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    run_demo()
