import streamlit as st
import openai
import time
import json
from pathlib import Path

from templates.prompt_template import get_system_prompt, get_feedback_prompt, get_system_prompt_fewshot_mean

# Create a directory for logs/debug outputs (optional)
Path("debug_logs").mkdir(exist_ok=True)

# ----------------------------------------
# Initialize session state variables
# ----------------------------------------
if "job_description" not in st.session_state:
    st.session_state.job_description = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "questions" not in st.session_state:
    st.session_state.questions = []

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

if "answers" not in st.session_state:
    st.session_state.answers = []

if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = []

if "awaiting_answer" not in st.session_state:
    st.session_state.awaiting_answer = False

if "ready_for_next" not in st.session_state:
    st.session_state.ready_for_next = False

#Clean configuration
#-----------------------------------------
ts = time.localtime()
ct = f"ts_{ts.tm_hour}{ts.tm_min}{ts.tm_sec}_{ts.tm_year}{ts.tm_mon}{ts.tm_mday}"
debug_filename = f"debug_logs/{ct}_debug_output.txt"
model = "gpt-3.5-turbo"  # Default model
temperature = 0.8  # Default temperature
top_p = 0.95  # Default top_p

#Sidebar configuration
#------------------------------------------
with st.sidebar:
    st.title('💬 Configuration')
    if 'OPENAI_API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        openai.api_key = st.secrets['OPENAI_API_KEY']
    else:
        openai.api_key = st.text_input('Enter OpenAI API token:', type='password')
        if not (openai.api_key.startswith('sk-') and len(openai.api_key)==51):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to Interview!', icon='👉')
    
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

    st.divider()
    st.write("Awaiting answer:", st.session_state.awaiting_answer)
    st.write("Ready for next:", st.session_state.ready_for_next)


# OpenAI model and parameters
#----------------------------------------
model = model if 'model' in locals() else "gpt-3.5-turbo"
temperature = temperature if 'temperature' in locals() else 0.8
top_p = top_p if 'top_p' in locals() else 0.95


# ----------------------------------------
#  Step 1: Job description input
# ----------------------------------------
st.title("🧠 AI Job Interviewer")

st.subheader("Step 1: Paste a Job Description")
job_description_input = st.text_area("Paste the job description here", height=400)

if st.button("Start Interview"):
    if not job_description_input.strip():
        st.warning("Please paste a job description first.")
    else:
        # Save job description
        st.session_state.job_description = job_description_input
        st.session_state.interview_started = True
        st.session_state.messages = [{"role": "system", "content": get_system_prompt_fewshot_mean(job_description_input)}]
        st.session_state.questions = []
        st.session_state.current_question_index = 0
        st.session_state.awaiting_answer = False

        # Step 2: Generate interview questions
        with st.spinner("Generating interview questions..."):
            response = openai.chat.completions.create(
                model=model,
                messages=st.session_state.messages + [ # type: ignore
                    {"role": "user", "content": "Please generate the 5 interview questions now, without asking them yet. Just list them."}
                ],
                temperature=temperature,
                top_p=top_p,
            )
            q_text = response.choices[0].message.content

        # Extract questions from AI response (simple split by line)
        st.session_state.questions = [
            line for line in q_text.split("\n") if line.strip() and line.strip()[0].isdigit() # type: ignore
        ]

        # Add summary to history
        st.session_state.messages.append({"role": "user", "content": "Please generate the 5 interview questions now, without asking them yet. Just list them."})
        st.session_state.messages.append({"role": "assistant", "content": q_text}) # type: ignore

# ----------------------------------------
# 4. Step 2: Interview in progress
# ----------------------------------------
if st.session_state.interview_started and st.session_state.questions:
    idx = st.session_state.current_question_index

    # Show all previous questions, answers, and feedbacks
    for i in range(len(st.session_state.answers)):
        st.markdown(f"#### Question {i+1}")
        st.markdown(f"**{st.session_state.questions[i]}**")
        st.markdown(f"**Your answer:** {st.session_state.answers[i]}")
        st.markdown(f"**Feedback:** {st.session_state.feedbacks[i]}")

    st.divider()
    st.subheader(f"Question {idx + 1} of {len(st.session_state.questions)}")
    question = st.session_state.questions[idx]
    st.markdown(f"**{question}**")
    st.session_state.awaiting_answer = True

# Show the input box only when waiting for user answer
#-----------------------------------------
if st.session_state.awaiting_answer:
    user_input = st.chat_input("Your answer:")

    if user_input:
         # Save the answer
        st.session_state.answers.append(user_input)

        # Append user answer to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Show current question and user's answer BEFORE feedback
        st.markdown(f"### Question {idx + 1}")
        st.markdown(f"**{st.session_state.questions[idx]}**")
        st.markdown(f"**Your answer:** {user_input}")

        # Ask assistant to give feedback only
        feedback_prompt = get_feedback_prompt(user_input, idx)
        
        st.session_state.messages.append({"role": "user", "content": feedback_prompt})
        # Lock input and show Next button
        st.session_state.awaiting_answer = False
        

        # Stream AI feedback
        with st.chat_message("assistant"):
            full_response = ""
            response_placeholder = st.empty()
            for chunk in openai.chat.completions.create( # type: ignore
                model=model,
                messages=st.session_state.messages, # type: ignore
                temperature=temperature,
                top_p=top_p,
                stream=True
            ):
                if hasattr(chunk.choices[0].delta, "content"):
                    full_response += chunk.choices[0].delta.content or ""
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.feedbacks.append(full_response)   

            #st.session_state.ready_for_next = True  # Wait for user trigger
            st.session_state.awaiting_answer = False
            st.session_state.ready_for_next = True       

            # Show "Next Question" button if feedback has been given
            if st.session_state.ready_for_next and st.session_state.current_question_index < len(st.session_state.questions) - 1:
                if st.button("➡️ Next Question"):
                    st.session_state.current_question_index += 1
                    st.session_state.awaiting_answer = True
                    st.session_state.ready_for_next = False
                    st.rerun()
            elif st.session_state.current_question_index == len(st.session_state.questions) - 1 and st.session_state.ready_for_next:
                st.success("🎉 Interview complete!")

        
        # Move to next question if any
        st.session_state.current_question_index += 1
        if st.session_state.current_question_index < len(st.session_state.questions):
             st.session_state.awaiting_answer = True
        else:
            st.success("✅ Interview complete!")
            st.session_state.awaiting_answer = False
