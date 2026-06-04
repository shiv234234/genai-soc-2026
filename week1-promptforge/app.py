from groq import Groq
import gradio as gr
import os
from dotenv import load_dotenv
import json
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

modes = {
    "Technical Explainer": {
        "system_prompt": "You are a concise technical explainer. Explain complex concepts clearly to undergraduates, avoiding unnecessary jargon. Keep responses under 100 words.",
        "few_shot_examples": [
            {"role": "user", "content": "What is a neural network?"},
            {"role": "assistant", "content": "A neural network is a type of machine learning model inspired by the structure of the human brain. It consists of layers of interconnected 'neurons' that process data. Each connection has a weight that adjusts during training, allowing the network to learn patterns and make predictions from input data."},
            {"role": "user", "content": "Explain recursion."},
            {"role": "assistant", "content": "Recursion is a programming technique where a function calls itself to solve a smaller instance of the same problem. Think of it like a set of Russian nesting dolls: you open one to find a smaller one inside, repeating the process until you reach the smallest doll, which is your base case."}
        ],
        "output_format": "text"
    },
    "Debate Coach": {
        "system_prompt": "You are a skilled debate coach. For any topic provided, present the strongest arguments for both the 'Pro' and 'Con' sides objectively.",
        "few_shot_examples": [
            {"role": "user", "content": "Should companies use remote work?"},
            {"role": "assistant", "content": "**Pro:** Increases employee flexibility and access to a global talent pool. \n**Con:** Can lead to reduced team cohesion and difficulty in managing corporate culture."},
            {"role": "user", "content": "Is space exploration worth the cost?"},
            {"role": "assistant", "content": "**Pro:** Drives technological innovation and scientific discovery that benefits Earth. \n**Con:** Extremely expensive with no guaranteed immediate return on investment for the general public."}
        ],
        "output_format": "text"
    },
    "Code Reviewer": {
        "system_prompt": "You are a strict code reviewer. Identify bugs and suggest improvements. Respond ONLY with valid JSON in this format: {\"issues\": [], \"suggestions\": [], \"severity\": \"low|medium|high\"}. Do not include markdown fences or preamble.",
        "few_shot_examples": [
            {"role": "user", "content": "print('hello'"},
            {"role": "assistant", "content": "{\"issues\": [\"SyntaxError: missing closing parenthesis\"], \"suggestions\": [\"Add a closing parenthesis at the end of the print statement.\"], \"severity\": \"high\"}"},
            {"role": "user", "content": "x = 10 / 0"},
            {"role": "assistant", "content": "{\"issues\": [\"ZeroDivisionError: division by zero\"], \"suggestions\": [\"Add a check to ensure the denominator is not zero before performing division.\"], \"severity\": \"high\"}"}
        ],
        "output_format": "json"
    },
    "Creative Writer": {
        "system_prompt": "You are a creative writer who uses a vivid, descriptive, and narrative style. Bring every scene and concept to life with sensory details.",
        "few_shot_examples": [
            {"role": "user", "content": "Describe a thunderstorm."},
            {"role": "assistant", "content": "The sky bruised into a deep, angry purple before the clouds tore open. Thunder growled like a beast waking from a long slumber, and rain hammered against the roof like thousands of tiny, frantic knuckles demanding entry."},
            {"role": "user", "content": "Describe a morning in a library."},
            {"role": "assistant", "content": "Dust motes danced in the shafts of golden morning light piercing the tall, stained-glass windows. The air smelled of aged parchment, leather bindings, and the quiet promise of untold stories, undisturbed by the world outside."}
        ],
        "output_format": "text"
    }
}
import json

def process_code_review(raw_response):
    """
    Parses the LLM string output and returns a formatted Markdown string.
    """
    try:
        # Attempt to parse the string into a dictionary
        data = json.loads(raw_response)
        
        # Build the Markdown formatted string
        markdown_output = f"### 🔍 Code Review Results\n\n"
        markdown_output += f"**Severity:** {data.get('severity', 'N/A').upper()}\n\n"
        
        markdown_output += "**Issues:**\n"
        for issue in data.get('issues', []):
            markdown_output += f"- {issue}\n"
            
        markdown_output += "\n**Suggestions:**\n"
        for suggestion in data.get('suggestions', []):
            markdown_output += f"- {suggestion}\n"
            
        return markdown_output

    except json.JSONDecodeError:
        # If parsing fails, return raw response with a warning
        return f"⚠️ **Warning:** Could not parse JSON. Raw output below:\n\n{raw_response}"

def chat_stream(message, history,dropDown,slider):
    
    mode  = dropDown
    messages = [{"role": "system", "content": modes[mode]["system_prompt"]}]
    messages.extend(modes[mode]["few_shot_examples"])
    # include conversation history
    for msg in history:
        messages.append({"role": msg["role"], "content": msg['content'][0]['text']})
        
    messages.append({"role": "user", "content": message})
    isCodeReviewer = (mode == "Code Reviewer")
    stream = client.chat.completions.create(
        temperature=slider,
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=not(isCodeReviewer),   # key line — enables streaming
    )
    accumulated = ""
    jsonTxt = ""
    if(mode == "Code Reviewer"):
            jsonTxt = stream.choices[0].message.content
            markdownTxt = process_code_review(jsonTxt)
            yield markdownTxt;
    else:
        
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            accumulated += delta
            yield accumulated   # Gradio re-renders on each yield

# One-line chat UI with streaming built in
MODE_DESCRIPTIONS = {
    "Technical Explainer": "This mode simplifies complex technical concepts into clear, jargon-free explanations.",
    "Debate Coach": "This mode provides a balanced perspective by outlining both affirmative and negative arguments on any given topic.",
    "Code Reviewer": "This mode analyzes code snippets to identify potential issues and provides structured, actionable improvement suggestions.",
    "Creative Writer": "This mode focuses on narrative depth, using vivid imagery and descriptive language to bring stories to life."
}
def reset():
    return [], []
def showMode(mode):
    return MODE_DESCRIPTIONS[mode]
with gr.Blocks(title = "mini project") as demo:
    bot = gr.Chatbot(render=False)
    with gr.Accordion(label = "Settings"):
        dropDown = gr.Dropdown(choices=["Technical Explainer","Debate Coach","Code Reviewer","Creative Writer"],label = "Mode",interactive=True)
        
        
        out = gr.Textbox(label = "mode description",value = MODE_DESCRIPTIONS["Technical Explainer"],interactive= False)
        dropDown.change(showMode,inputs= dropDown,outputs=out)
        slider = gr.Slider(minimum = 0.0,maximum=2.0,step = 0.1,label = "Temperatue",value= 0.7)
    chat = gr.ChatInterface(
        fn=chat_stream,
        additional_inputs=[
            dropDown,slider
            
        ],
        title = "PromptForge",
        
    )
    dropDown.input(reset,inputs = None,outputs=[bot,chat.chatbot_state])
    
demo.launch(share = True)