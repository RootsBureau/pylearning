import streamlit as st
import openai
import json
from pathlib import Path
#import random
import time

from templates.prompt_template import get_system_prompt


# Create a directory for logs/debug outputs (optional)
Path("debug_logs").mkdir(exist_ok=True)

#Clean configuration
ts = time.localtime()
ct = f"ts_{ts.tm_hour}{ts.tm_min}{ts.tm_sec}_{ts.tm_year}{ts.tm_mon}{ts.tm_mday}"
debug_filename = f"debug_logs/{ct}_debug_output.txt"
model = "gpt-3.5-turbo"  # Default model
temperature = 0.8  # Default temperature
top_p = 0.95  # Default top_p

#Sidebar configuration
with st.sidebar:
    st.title('🤖💬 OpenAI Chatbot')
    if 'OPENAI_API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        openai.api_key = st.secrets['OPENAI_API_KEY']
    else:
        openai.api_key = st.text_input('Enter OpenAI API token:', type='password')
        if not (openai.api_key.startswith('sk-') and len(openai.api_key)==51):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    
    st.divider()
    
    #Settings form in the sidebar
    with st.form(key="settings_form"):
        st.subheader("Settings")
        model = st.selectbox(
            "Select Model",
            options=["gpt-3.5-turbo", "gpt-4", "o4-mini", "ChatGPT-4o"],
            index=0,
            help="Choose the model you want to use for the chatbot."
        )
            
        temperature = st.slider(
            "Temperature",
            min_value=0.1,
            max_value=0.9,
            value=0.8,
            step=0.1,
            help="Controls the randomness of the model's responses."
            )
        top_p = st.slider(
            "Top P",
            min_value=0.7,
            max_value=0.99,
            value=0.95,
            step=0.01,
            help="Controls the randomness of text generation."
            )

        submit_button = st.form_submit_button(label="Update Settings")
        if submit_button:
            openai.api_key = openai.api_key            
            st.success(f"Settings updated! Model: {model}, Temperature: {temperature}", icon='✅')

#TODO: Add output of parameters in the sidebar
#with st.sidebar:
#    st.expander("🔍 Params Output", expanded=False)
#      st.write(model, " temperature: ", temperature, "top p :", top_p)
                 
system_prompt = "You are very angry job interviewer. You are very rude and you don't like to answer questions. You are very sarcastic and you don't like to help people."

# OpenAI model and parameters
model = model if 'model' in locals() else "gpt-3.5-turbo"
temperature = temperature if 'temperature' in locals() else 0.8
top_p = top_p if 'top_p' in locals() else 0.95

#Welcome Meessage
st.title("Welcome to the Chatbot!")
st.markdown(               
                """                
                This is a simple chatbot interface built with Streamlit. 
                You can interact with it by typing your messages below. Enjoy!
                ## How to use:
                1. Type your message in the input box.
                2. Press Enter to send your message.
                3. The chatbot will respond to your message.               
                """
                )
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
         st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        debug_container = st.expander("🔍 Raw Debug Output", expanded=False)
        raw_chunks = []        
        full_response = ""

        # Build the message list
        messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        for response in openai.chat.completions.create(
            model=model,
            messages=messages, # type: ignore
            temperature=temperature,
            top_p=top_p,
            stream=True
        ): # type: ignore
            raw_chunks.append(response)  # Save raw chunk            
            if hasattr(response.choices[0].delta, "content"):
                full_response += response.choices[0].delta.content or ""
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

        #Saves raw response chunks to a file for debugging
        with open(debug_filename, "w", encoding="utf-8") as f:
            json.dump([chunk.model_dump() for chunk in raw_chunks], f, ensure_ascii=False, indent=2)
        
        # Output raw chunks as debug info
        with debug_container:
            for i, chunk in enumerate(raw_chunks):
                #st.code(repr(chunk), language="python")
                st.json(json.loads(chunk.model_dump_json()))

    st.session_state.messages.append({"role": "assistant", "content": full_response})


    

