import streamlit as st
import streamlit_survey as ss
import uuid
import datetime
import boto3

session = boto3.Session()
dynamodb = session.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('chatbot_feedback')

def main():
    st.set_page_config(page_title="Faber - Feedback",
                       page_icon="assets/chatbotlogocropped.png")

    st.header("Review previous responses")

    try:
        if len(st.session_state.messages) > 1:
            qna_pairs = []
            for i in range(1, len(st.session_state.messages), 2): # skip first question as it's bot intro
                pair = (st.session_state.messages[i], st.session_state.messages[i+1])
                qna_pairs.append(pair)

            survey = ss.StreamlitSurvey("Survey")
            # Survey pages
            npages = int(len(qna_pairs))
            page = survey.pages(npages, on_submit=lambda: st.success("Your responses have been recorded. Thank you!"))

            with page:
                """#### Chat"""
                for message in qna_pairs[page.current]:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
                
                # Insert the Q&A pair in the survey data to be exported
                qna_pair_id = f"qnapair_{page.current}"
                qna_pair = {"label": "QA Pair", "value": qna_pairs[page.current]}
                st.session_state['__streamlit-survey-data_Survey'][qna_pair_id] = qna_pair


                """#### Review"""
                col1, col2 = st.columns([1, 2])
                with col1:
                    survey.text_input("User alias:")
                with col2:
                    like = survey.select_slider( 
                        "Likert scale:",
                        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                        id=f"like{page.current}"
                        )
                survey.text_area(
                    "Notes", 
                    id=f"notes_{page.current}"
                    )

            # On submit save the feedback in the database
            if st.session_state.get('__streamlit-survey-data_Survey_Pages__btn_submit') is not None:
                if st.session_state.get('__streamlit-survey-data_Survey_Pages__btn_submit') == True:
                    json = survey.to_json()
                    table.put_item(
                        Item={
                            'datetime': str(datetime.datetime.now()),
                            'SessionId': str(uuid.uuid1()),
                            'info': json})
        else:
            """##### The conversation history is empty, start chatting with the bot and come back!"""
    except AttributeError:
        """##### Start a conversation session and come back to provide your feedback 🙂"""

if __name__ == '__main__':
    main()