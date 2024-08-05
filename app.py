import os
from time import sleep
from random import choice
from typing import AsyncGenerator, Generator, Any, List

import streamlit as st
from streamlit_feedback import streamlit_feedback

from langserve import RemoteRunnable

from langfuse import Langfuse

import asyncio

TITLE = "PumpPal (Beta) - Heatpump Installer Assistant"
MODEL_NAME = os.environ.get("MODEL_NAME")
TEMPERATURE = float(os.environ.get("TEMPERATURE"))

st.set_page_config(page_title=TITLE)
#st.title(TITLE)
#st.subheader("Hey! Pleasure to meet you, I'm PumpPal your very own heat pump AI assistant. I'm currently in a Beta version, but I have information regarding installation manuals, a plumbing textbook and UK domestic heat pump best practice guidance.")

# Initialize chatbot chain endpoint
hpi_chatbot_chain = RemoteRunnable(url=os.environ.get("CHATBOT_URL"))

# Initialize Langfuse client
langfuse_client = Langfuse()

# Initial message
convo_starters = [
    "Can I assist you with anything today?",
    "What would you like to know about heatpumps?",
    "What heatpump query do you have?",
    "What do you want to know about heatpumps?",
]

def convo_starter_generator(
    convo_starters: List[str] = convo_starters,
    chunk_delay: float = os.environ.get("CHUNK_DELAY", 0.05)
) -> Generator[str, None, None]:
    """
    Generates a stream from a randomly chosen conversation starter message.
    If there is only one option for the conversation starter, it will be chosen.

    Args:
        convo_starters (List[str], optional): List of conversation starter messages. Defaults to convo_starters.

    Yields:
        str: Generator chunk of randomly chosen conversation starter message.
    """
    response = choice(convo_starters) if len(convo_starters) > 1 else convo_starters[0]
    for word in response.split():
        yield word + " "
        sleep(chunk_delay)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.chat_message("assistant"):
        response = st.write_stream(
            convo_starter_generator(
                [
                    "Hey! Pleasure to meet you, I'm PumpPal, your very own heat pump AI assistant. I'm currently in a Beta version, but I have information regarding installation manuals, a plumbing textbook and UK domestic heat pump best practice guidance. " + convo_starters[0]
                ]
            )
        )
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "feedback" in message:
                st.markdown(message["feedback"]["score"])

async def achain_response_generator(
    query: str,
    chunk_delay: float = os.environ.get("CHUNK_DELAY", 0.05)
) -> AsyncGenerator[str, None]:
    """
    Asynchronously generates a stream of response events from the chatbot chain endpoint query request.
    Each event chunk contains an "answer" key. Streamed response is from the endpoint chain,
    not LLM, so this function yields relevant events from stream, and caches last run_id.

    Args:
        query (str): User query to the chatbot chain endpoint.

    Yields:
        Union[str, Any]: Streamed chunk of assistant response to user query, where the event chunk contains an "answer" key, or the chunk itself if it has a "run_id" key.
    """
    # add generation call here
    async for chunk in hpi_chatbot_chain.astream_events(
        input=query,
        config={
            "configurable": {
                "model_name": MODEL_NAME,
                "temperature": TEMPERATURE,
            }
        },
        version="v1",
        include_names=["StrOutputParser"],
    ):
        # Cache last generation run_id
        if chunk["event"] == "on_start_start":
            st.session_state.run_id = chunk["run_id"]

        if chunk["event"] == "on_start_stream":
            yield chunk["data"]["chunk"]
            sleep(chunk_delay)

def to_sync_generator(async_gen: AsyncGenerator):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        while True:
            try:
                yield loop.run_until_complete(anext(async_gen))
            except StopAsyncIteration:
                break
    finally:
        loop.close()

# Accept user input
if prompt := st.chat_input("Enter your query here..."):
    # Add user message to chat history
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(
            to_sync_generator(achain_response_generator(prompt))
        )

    with st.chat_message("assistant"):

        run_id = st.session_state.run_id
        st.write(run_id)
        feedback_key = f"feedback_{run_id}"

        def _on_submit(feedback):
            # Define score mappings for both "thumbs" and "faces" feedback systems
            score_mappings = {
                "thumbs": {"👍": 1, "👎": 0},
                "faces": {"😀": 1, "🙂": 0.75, "😐": 0.5, "🙁": 0.25, "😞": 0},
            }

            # Get the score mapping based on the selected feedback option
            scores = score_mappings["faces"]

            if not feedback:
                raise Exception("feedback isn't working")
            else:
                # Get the score from the selected feedback option's score mapping
                score = scores.get(feedback["score"])
                comment = feedback.get("text")

                if score is not None:
                    langfuse_client.score(
                        trace_id=run_id,
                        name="user_feedback",
                        data_type="NUMERIC",
                        score=score,
                        comment=comment,
                    )

                    st.session_state.feedback = {
                        "feedback_id": feedback_key,
                        "score": score,
                    }
                else:
                    st.warning("Invalid feedback score.")
            return {
                "score": score,
                "feedback": comment,
            }
                

        feedback = streamlit_feedback(
            feedback_type="faces",
            optional_text_label="[Optional] Please provide an explanation",
            key=feedback_key,
            on_submit=_on_submit
        )


        mock_feedback = {
            "score": 3,
            "feedback": "testing"
        }
        
        langfuse_client.score(
            trace_id=run_id,
            name="user_feedback",
            data_type="NUMERIC",
            score=score,
            comment=comment,
        )

        feedback=mock_feedback

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response, "feedback": feedback})
