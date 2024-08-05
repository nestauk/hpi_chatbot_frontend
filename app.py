import os
from time import sleep
from random import choice
from pathlib import Path
from typing import AsyncGenerator, Generator, List

import streamlit as st
from streamlit_feedback import streamlit_feedback
from streamlit_extras.stylable_container import stylable_container

from langserve import RemoteRunnable

from langfuse import Langfuse

import asyncio

from functools import partial

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
        include_names=["RunnableSequence"],
    ):
        if (
            (chunk["event"] == "on_chain_stream")
            and ("chunk" in chunk["data"])
            and ("answer" in chunk["data"]["chunk"])
        ):
            yield chunk["data"]["chunk"]["answer"]
            sleep(chunk_delay)

        # Cache last generation run_id
        if (chunk["event"] == "on_chain_start") and ("input" in chunk["data"]):
            st.session_state.run_id = chunk["run_id"]

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

## Themed
if "theme" in st.query_params:
    bot = "Renbee"
    themes_path = Path(__file__).parent / "themes"
    with open(themes_path / f'{st.query_params["theme"]}.css') as f:
        st.markdown('<style>' + f.read() + '</style>', unsafe_allow_html=True)

    # Note: container key needs to be "somewhat" unique depending on purpose
    bot_chat_container = partial(
        stylable_container,
        css_styles=[
            """
            .st-emotion-cache-1dgsum0 {
                display: flex;
                width: 2rem;
                height: 2rem;
                flex-shrink: 0;
                border-radius: 0.5rem;
                -webkit-box-align: center;
                align-items: center;
                -webkit-box-pack: center;
                justify-content: center;
                border: 1px solid rgba(20, 81, 100, 1);
                background-color: rgba(20, 81, 100, 1);
                color: rgb(255, 255, 255);
                line-height: 1;
                font-size: 1rem;
            }
            """,
            """
            div[data-testid="stChatMessage"] {
                background-color: rgba(240, 242, 246, 0.5);
            }
            """,
        ]
    )

    user_chat_container = partial(
        stylable_container,
        css_styles=[
            """
            .st-emotion-cache-1dgsum0 {
                display: flex;
                width: 2rem;
                height: 2rem;
                flex-shrink: 0;
                border-radius: 0.5rem;
                -webkit-box-align: center;
                align-items: center;
                -webkit-box-pack: center;
                justify-content: center;
                border: 1px solid gray;
                background-color: gray;
                color: rgb(255, 255, 255);
                line-height: 1;
                font-size: 1rem;
            }
            """,
            """
            div[data-testid="stChatMessage"] {
                background-color: rgb(255, 255, 255);
                opacity: 0.4;
            }
            """,
        ]
    )

    # Initialize chat history
    # Purpose of styled containers here is to contain the intro message generation
    if "messages" not in st.session_state:
        st.session_state.messages = []
        with bot_chat_container(key="intro_bot_msg"):
            with st.chat_message(bot):
                response = st.write_stream(
                    convo_starter_generator(
                        [
                            "Hey! Pleasure to meet you, I'm PumpPal, your very own heat pump AI assistant. I'm currently in a Beta version, but I have information regarding installation manuals, a plumbing textbook and UK domestic heat pump best practice guidance. " + convo_starters[0]
                        ]
                    )
                )

                st.session_state.messages.append({"role": "assistant", "content": response})

    # Purpose here is to contain historical messages that are unique
    # to the incrementing order that they were appended to in session_state
    else:
        message_id = 0
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with bot_chat_container(key=f"bot_msg_{message_id}"):
                    with st.chat_message(name=bot):
                        st.markdown(message["content"])

            else:
                with user_chat_container(key=f"user_msg_{message_id}"):
                    with st.chat_message(name="user", avatar=":material/engineering:"):
                        st.markdown(message["content"])
            message_id += 1

    # Purpose of styled containers here is to print the markdown of a new user input
    # and stream the new LLM-chain response. These will be overwritten by newer messages.
    # Accept user input
    if prompt := st.chat_input("Enter your query here..."):
        with user_chat_container(key=f"user_msg_new"):
            with st.chat_message("user", avatar=":material/engineering:"):
                st.markdown(prompt)

                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with bot_chat_container(key=f"bot_msg_new"):
            with st.chat_message(bot):
                response = st.write_stream(
                    to_sync_generator(achain_response_generator(prompt))
                )

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})

                if "feedback" not in st.session_state:
                    st.session_state["feedback"] = None
        with stylable_container(key="feedback_container", css_styles=[""]):
            feedback = streamlit_feedback(
                feedback_type="faces",
                optional_text_label="[Optional] Please provide an explanation",
                key="feedback",
            )

## Default app
else:
    bot = "assistant"

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        with st.chat_message(bot):
                response = st.write_stream(
                    convo_starter_generator(
                        [
                            "Hey! Pleasure to meet you, I'm PumpPal, your very own heat pump AI assistant. I'm currently in a Beta version, but I have information regarding installation manuals, a plumbing textbook and UK domestic heat pump best practice guidance. " + convo_starters[0]
                        ]
                    )
                )

                st.session_state.messages.append({"role": "assistant", "content": response})
    # Display chat messages from history on app rerun
    else:
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message(name=bot):
                    st.markdown(message["content"])
            else:
                with st.chat_message(name="user", avatar=":material/engineering:"):
                    st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Enter your query here..."):
        with st.chat_message("user", avatar=":material/engineering:"):
            st.markdown(prompt)

            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message(bot):
            response = st.write_stream(
                to_sync_generator(achain_response_generator(prompt))
            )

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            if "feedback" not in st.session_state:
                st.session_state["feedback"] = None
        with stylable_container(key="feedback_container", css_styles=[""]):
            feedback = streamlit_feedback(
                feedback_type="faces",
                optional_text_label="[Optional] Please provide an explanation",
                key="feedback",
            )

# add user feedback as a score
if ("feedback" in st.session_state) and (st.session_state["feedback"] is not None):
    emoji = st.session_state["feedback"]["score"]
    scores_mapping = {"😀": 5, "🙂": 4, "😐": 3, "🙁": 2, "😞": 1}
    score = scores_mapping.get(emoji)
    langfuse_client.score(
        trace_id=st.session_state["run_id"],
        name="user_feedback",
        data_type="NUMERIC",
        value=score,
        comment=f'{emoji} {st.session_state["feedback"]["text"]}',
    )
