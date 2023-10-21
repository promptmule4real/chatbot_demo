import os
import asyncio
import httpx  # Used for asynchronous HTTP requests
import chainlit as cl  # Used for chatbot functionality

# Retrieve the Promptmule API key from the environment variables
PROMPTMULE_API_KEY = os.environ.get("PROMPTMULE_API_KEY")

# Define the Promptmule API endpoint
PROMPTMULE_ENDPOINT = "https://api.promptmule.com/prompt"

@cl.on_chat_start
async def start_chat():
    """
    Initialize the chat session, set the initial message history,
    and send avatars for the characters.
    """
    # Set the initial message history in the user session
    cl.user_session.set(
        "message_history",
        [
            {
                "role": "system",
                "content": "Characters from the Silicon Valley TV show are acting. Gilfoyle (sarcastic) wants to push to production. Dinesh (scared) wants to write more tests. Richard asks the question."
            }
        ]
    )

    # Send avatar images for the characters
    await cl.Avatar(name="Gilfoyle", url="https://static.wikia.nocookie.net/silicon-valley/images/2/20/Bertram_Gilfoyle.jpg").send()
    await cl.Avatar(name="Dinesh", url="https://static.wikia.nocookie.net/silicon-valley/images/e/e3/Dinesh_Chugtai.jpg").send()

async def make_promptmule_request(message_history):
    """
    Make an asynchronous request to the Promptmule API to generate a response based on the message history.

    Args:
    message_history (list): A list of previous messages exchanged during the chat session.

    Returns:
    dict: A dictionary containing the API response.
    """
    # Define the headers for the API request
    headers = {
        "Content-Type": "application/json",
        "x-api-key": PROMPTMULE_API_KEY  # API key for authentication
    }
    
    # Define the data payload for the API request
    data = {
        "model": "gpt-3.5-turbo",  # Specify the model to use for text generation
        "messages": message_history,  # Include the message history as context for the generation
        "max_tokens": "100",  # Limit on the number of tokens in the generated response
        "temperature": "0.3",  # Creative freedom in the generated text
        "api": "openai",  # Backend AI provider
        "semantic": "0.95",  # Semantic matching control
        "sem_num": "2"  # Number of semantic matches to return
    }

    # Define a 10-second timeout for the request
    timeout = httpx.Timeout(10.0)

    # Perform the asynchronous POST request
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(PROMPTMULE_ENDPOINT, headers=headers, json=data)

    # If the request was successful, return the JSON response
    if response.status_code == 200:
        return response.json()
    else:
        # If the request failed, return a dictionary containing the error
        return {"error": response.text}

async def answer_as(name):
    """
    Generate and send a message as a specific character based on the chat history.

    Args:
    name (str): The name of the character who is responding.
    """
    # Retrieve the message history from the user session
    message_history = cl.user_session.get("message_history")

    # Create a new message object for the response
    msg = cl.Message(author=name, content="")

    # Request a message generation from the Promptmule API
    token = await make_promptmule_request(message_history)

    # If the API response contains valid choices, use the first choice
    if 'choices' in token and token['choices']:
        content_text = token['choices'][0]['message']['content']
        await msg.stream_token(content_text)

        # Append the generated message to the message history
        message_history.append({"role": "assistant", "content": content_text})
        await msg.send()
    else:
        # Log an error if the API response is unexpected
        print(f"Unexpected response: {token}")
        # Additional error handling can be added here

@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages by updating the message history and initiating character responses.

    Args:
    message (cl.Message): The incoming message object.
    """
    # Retrieve the message history from the user session
    message_history = cl.user_session.get("message_history")

    # Add the incoming message to the beginning of the message history
    message_history.insert(0, {"role": "user", "content": message.content})

    # Initiate responses from the characters Gilfoyle and Dinesh
    await asyncio.gather(answer_as("Gilfoyle"), answer_as("Dinesh"))
