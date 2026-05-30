import gradio as gr
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_stream(message, history):
    """Gradio chat function — yields accumulated text for streaming display."""
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    # include conversation history
    for msg in history:
        messages.append({"role": msg["role"],      "content": msg['content'][0]['text']})
        
    messages.append({"role": "user", "content": message})

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,   # key line — enables streaming
    )

    accumulated = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        accumulated += delta
        yield accumulated   # Gradio re-renders on each yield

# One-line chat UI with streaming built in
gr.ChatInterface(
    fn=chat_stream,
    title="My First AI Chat App",
).launch()