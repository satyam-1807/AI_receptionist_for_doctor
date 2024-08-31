import time
import random
from openai import OpenAI

# Global variable to store chat history
chat_history = [{"role": "assistant", "content": "Hello. I am Roohi, receptionist of Dr. Adrin. How may I assist you today?"}]

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


def call_gpt(prompt):
    global chat_history
    chat_history.append({"role": "user", "content": prompt})

    client = OpenAI()
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=chat_history
    )
    # Append GPT's response to the chat history
    assistant_message = response.choices[0].message.content.strip() 
    chat_history.append({"role": "assistant", "content": assistant_message})
    
    return assistant_message

# Simulate a vector database of emergency instructions
emergency_database = {
    "not_breathing": "Start CPR immediately. Push down hard and fast in the center of the chest, 100 to 120 compressions per minute.",
    "chest_pain": "Keep the patient calm and seated, administer aspirin if available.",
    "bleeding": "Apply pressure to the wound to stop the bleeding, elevate the wound if possible.",
    "others": "Stay calm and describe the symptoms in detail."
}

# Function to detect sub-intent using GPT-4
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
def handle_emergency(user_input):
    emergency_type = detect_sub_intent(user_input)

    while emergency_type == "general":
        node1 = "Please describe your emergency: (e.g., not able to breath, chest pain, bleeding, others)"
        print(node1)
        chat_history.append({"role": "assistant", "content": node1})
        user_input = input()
        chat_history.append({"role": "user", "content": user_input})
        emergency_type = detect_sub_intent(user_input)

    start_time = time.time() #start_time for artificial delay
    node2 = "I am checking what you should do immediately, meanwhile, can you tell me which area you are located in right now?"
    print(node2)
    chat_history.append({"role": "assistant", "content": node2})
    user_input = input()
    chat_history.append({"role": "user", "content": user_input})
    
    node3 = f"Dr. Adrin will be coming to your location immediately. Estimated time of arrival: {random.randint(5, 15)} minutes."
    print(node3)
    chat_history.append({"role": "assistant", "content": node3})
    user_input = input()
    chat_history.append({"role": "user", "content": user_input})

    # Calculate the elapsed time
    while True:
        elapsed_time = time.time() - start_time
        instructions = emergency_database[emergency_type]    
        if elapsed_time >= 15:
            print(call_gpt(f"""The user is saying {user_input}. The instructions are {instructions}. If the user says the doctor will be late, reply 'I understand that you are worried that Dr. Adrin will arrive too late. Meanwhile, we suggest that you {instructions}' else just provide the instructions."""))
            break
        else:
            print("Please wait a sec")
            time.sleep(4)

# Function to handle leaving a message
def handle_message():
    response1 = "Please leave your message for Dr. Adrin:"
    print(response1)
    chat_history.append({"role": "assistant", "content": response1})
    message = input()
    chat_history.append({"role": "user", "content": message})
    #We can make an API here to append the msg to a google sheet or any other way though which Dr. Adrin can see the message
    response2 = "Thanks for the message, we will forward it to Dr. Adrin."
    print(response2)
    chat_history.append({"role": "user", "content": response2})


# Main conversation loop
def main():
    print("Hello. I am Roohi, receptionist of Dr. Adrin. How may I assist you today?")
    user_input = input()
    
    intent = detect_intent(user_input)
    # print(intent)
    if intent=="emergency":
        handle_emergency(user_input)
    elif intent=="leave_a_message":
        handle_message()
    else:
        print("I don’t understand that.")
        main()  # Repeat the process if the input is not understood

if __name__ == "__main__":
    main()
