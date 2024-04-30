import boto3
import streamlit as st
from utils.chain import chat, clear_memory
from utils.q_exists import check_question_existence
from streamlit.runtime.scriptrunner import get_script_run_ctx
import datetime
import base64

session = boto3.Session()
dynamodb = session.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('chatbot_history')
    
def main():

    st.set_page_config(page_title="Faber",
                       page_icon="assets/chatbotlogocropped.png"
                       )

    LOGO_IMAGE = "assets/chatbotlogocropped.png"

    st.markdown(
        """
        <style>
        .container {
            display: flex;
            flex-direction: column; /* Change flex direction to stack elements vertically */
            align-items: center;
            justify-content: center;
            height: 10vh; /* Set the container height to 10% of the viewport height */
            margin-bottom: 50px;
        }
        .logo-text {
            font-weight: 700 !important;
            font-size: 24px !important;
            text-align: center;
            margin-bottom: 0px; /* Reduce the margin between title and slogan */
        }
        .slogan {
            font-size: 20px; /* Smaller font size for the slogan */
            text-align: center;
        }
        .logo-img {
            height: 70px;
            width: 77px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="container">
            <img class="logo-img" width="177" height="170" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
            <p class="logo-text">Faber</p>
            <p class="slogan">Unifying Answers, Empowering Users</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initiate session id
    ctx = get_script_run_ctx()
    session_id = str(ctx.session_id)

    # Store LLM generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "Hi there, I'm Faber 🤖 Ask me a question!"},]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "Hey, how may I help you?"}]
        clear_memory()

    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    # User-provided prompt
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Check if question is part of the dataset used for fine-tuning Mistral 7B, 
                # if yes return the answer directly if not trigger RAG
                answer,score,images = check_question_existence(prompt)
                if score > 0.009: # 90% similarity 
                    response = answer
                    if images != "":
                        li = list(images.split(", "))
                        st.image(li, use_column_width=True)
                else:
                    response = chat(prompt)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)

    item={
        'datetime': str(datetime.datetime.now()),
        'SessionId': session_id,
        'session': st.session_state.messages
        }
    
    table.put_item(Item=item)

if __name__ == '__main__':
    main()