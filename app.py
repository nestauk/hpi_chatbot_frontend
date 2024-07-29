import os
from time import sleep
from random import choice
from typing import Generator, List

import streamlit as st

from langserve import RemoteRunnable

TITLE = "PumpPal (Beta) - Heatpump Installer Assistant"
MODEL_NAME = os.environ.get("MODEL_NAME")
TEMPERATURE = float(os.environ.get("TEMPERATURE"))

st.set_page_config(page_title=TITLE)
#st.title(TITLE)
#st.subheader("Hey! Pleasure to meet you, I'm PumpPal your very own heat pump AI assistant. I'm currently in a Beta version, but I have information regarding installation manuals, a plumbing textbook and UK domestic heat pump best practice guidance.")

# Initialize chatbot chain endpoint
hpi_chatbot_chain = RemoteRunnable(url=os.environ.get("CHATBOT_URL"))

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

def chain_response_generator(
    query: str,
    chunk_delay: float = os.environ.get("CHUNK_DELAY", 0.05)
) -> Generator[str, None, None]:
    """
    Generates a stream of response events from the chatbot chain endpoint query request.
    Each event chunk contains an "answer" key.

    Args:
        query (str): User query to the chatbot chain endpoint.

    Yields:
        str: Streamed chunk of assistant response to user query, where the event chunk contains an "answer" key.
    """
    # add generation call here
    for chunk in hpi_chatbot_chain.stream(
        input=query,
        config={
            "configurable": {
                "model_name": MODEL_NAME,
                "temperature": TEMPERATURE,
            }
        }
    ):
        if "answer" in chunk:
            yield chunk["answer"]
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
            # Streamed response is from the endpoint chain, not LLM, need to parse events from stream
            chain_response_generator(prompt)
        )

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        ai_message = st.write_stream(convo_starter_generator())
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
