import time
import random
from openai import OpenAI
import asyncio
import aioconsole
from qdrant_client import QdrantClient
import os
import env

# Global variable to store chat history
chat_history = [{"role": "system", "content": "You are a receptionist of Dr. Adrin."},
                {"role": "assistant", "content": "Hello. I am Roohi, receptionist of Dr. Adrin. How may I assist you today?"}]

qdrant_client = QdrantClient(
    url="add67a69-43d5-4bd9-b72b-194eba28b90a.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="AfCEWmPdM17JABsezQ45-ANIze_GvAf95vGv57dtpHaSpsZcDP-5ng",
)

# Function to initialize and call GPT-4 with chat history
def detect_intent(user_input):
    client = OpenAI()
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "system", "content": """
                    Detect the intent from the user input and provide one word intent. Don't add anything.
                    The intent can be only from the below list:
                    "intent_list": [
                        {'name': 'emergency', 'description': 'If the user has an emergency or needs help immediately'},
                        {'name': 'leave_a_message', 'description': "If the user wants to leave a message for the doctor'}
                        ]
                    Your role is to read through the user input, and decide the intent of the user.
                    Depending on your output, the right agent will be assigned as per the intent skill downstream.

                    Return "general" if user does not meet any scenarioes from the intent list"""},
                {"role": "user", "content": user_input}]
    )
    assistant_message = response.choices[0].message.content.strip()
    return assistant_message


def call_gpt(user_input, prompt):
    global chat_history
    chat_history.append({"role": "user", "content": user_input})


    client = OpenAI()
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=chat_history + [{"role": "system", "content": prompt}]
    )
    # Append GPT's response to the chat history
    assistant_message = response.choices[0].message.content.strip()
    chat_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message

def vectorize_query(query_text):
    client = OpenAI()

    response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small")

    embedding = response.data[0].embedding
    return embedding

async def query_qdrant(query_text):
    await asyncio.sleep(15)  # Artificial delay of 15 seconds
    response = qdrant_client.search(
        collection_name="default",
        query_vector=vectorize_query(query_text),  # This would be a vectorized representation of your query
        limit=1  # Get the top result
    )
    if response:
        # Extract the instructions from the response
        return response[0].payload['content']
    return None

def detect_sub_intent(user_input):
    client = OpenAI()
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "system", "content": """
                    Detect the intent from the user input and provide one word intent. Don't add anything.
                    The intent can be only from the below list:
                    "intent_list": [
                        {'name': 'not_breathing', 'description': 'Patient is unable to breath'},
                        {'name': 'chest_pain', 'description': "Patient is having pain in chest or nearby chest area'},
                        {'name': 'bleeding', 'description': "Patient is bleeding"},
                        {'name': 'others', 'description': "Other symptoms of emergency"}
                        ]
                    Your role is to read through the user input, and decide the intent of the user.
                    Depending on your output, the right agent will be assigned as per the intent skill downstream.

                    Return "general" if the patient has not clearly mentioned the type of his emergency""" },
                {"role": "user", "content": user_input}]
    )
    assistant_message = response.choices[0].message.content.strip()
    return assistant_message

# Function to handle emergency
async def handle_emergency(user_input):
    emergency_type = detect_sub_intent(user_input)

    while emergency_type == "general":
        node1 = call_gpt(user_input, f"""Ask the user to describe about the type of emergency e.g., not able to breath, chest pain, bleeding.
                                        Don't add anything on your own. Use the details from the prompt only""")
        print(node1)
        user_input = input()
        chat_history.append({"role": "user", "content": user_input})
        emergency_type = detect_sub_intent(user_input)

    query_task = asyncio.create_task(query_qdrant(emergency_type))

    node2 = call_gpt(user_input, f""" Tell the user that you are checking what you should do immediately, meanwhile, tell them to provide his current location for Dr.Adrin to reach.
                                        Don't add anything on your own. Use the details from the prompt only""")
    print(node2)
    user_input = await aioconsole.ainput()
    chat_history.append({"role": "user", "content": user_input})

    node3 = call_gpt(user_input, f""" Tell the user Dr. Adrin will be coming shortly. Also, provide a dummy time of arrival.
                                        Don't add anything on your own. Use the details from the prompt only""")
    print(node3)
    user_input = await aioconsole.ainput()
    chat_history.append({"role": "user", "content": user_input})

    start_time = time.time()
    if query_task.done():  # Check if query is already done
        instructions = query_task
    else:
        print("Please hold just a sec. I am still checking what you should do immediately.")
        instructions = await query_task  # Wait for the query to complete
    # print("Elapsed time = ",time.time()-start_time)
    print(call_gpt(user_input, f"""Tell the user the doctor will arrive soon. Provide the instructions to the user based on this criteria:
                    1. If the user is seems to be satisfied with the time, reply with "Don’t worry, please follow these steps, Dr. Adrin will be with you shortly” and provide the instructions in a proper format. Don't add anything else and just provide the instructions.
                    2. If the user is concerened about the doctor's arrival time, reply with "I understand that you are worried that Dr. Adrin will arrive too late. Meanwhile, we suggest that you to follow the instructions" and provide the instructions in a proper format.

                    The instructions are:
                    {instructions}
                    Don't add anything on your own. Use the details from the prompt only"""))

# Function to handle leaving a message
def handle_message(user_input):
    response1 = call_gpt(user_input, f"""The user wants to leave a meaasge. Ask the user to write the message and you will forward it to Dr. Adrin
                                        Don't add anything on your own. Use the details from the prompt only""")
    print(response1)
    message = input()
    chat_history.append({"role": "user", "content": message})
    #We can make an API here to append the msg to a google sheet or any other way though which Dr. Adrin can see the message
    response2 = call_gpt(user_input, f"""Thanks the user for the message and say you will forward it shortly. 
                                        Don't add anything on your own. Use the details from the prompt only""")
    print(response2)


# Main conversation loop
async def main():
    print("Hello. I am Roohi, receptionist of Dr. Adrin. How may I assist you today?")
    user_input = input()

    intent = detect_intent(user_input)
    # print(intent)
    if intent=="emergency":
        await handle_emergency(user_input)
    elif intent=="leave_a_message":
        handle_message(user_input)
    else:
        print("I don’t understand that.")
        await main()  # Repeat the process if the input is not understood

if __name__ == "__main__":
    asyncio.run(main())
