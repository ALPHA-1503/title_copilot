import openai
from typing import List, Tuple, Dict


# Function to format history
def history_format(history: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    if not isinstance(history, list):
        raise Exception("The history should be a list of tuples")

    history_openai = []
    for human, assistant in history:
        history_openai.append({"role": "user", "content": human})
        history_openai.append({"role": "assistant", "content": assistant})
    return history_openai

# Function to send a message to Mistral and get a response
def send_message_to_mistral(client, message: str, history: List[Tuple[str, str]], retry: bool) -> str:
    new_question = history_format(history)

    if retry:
        new_question.append({
            "role": "user",
            "content": f"""Your previous response was not correct. Please try again.
               REQUIREMENTS:
                Answer only with the title that I ask you to rephrase.
                8. Do not repeat the same title as before.
                9. Do not use quotation marks around your response.
                10. Do not answer a title that you already answered before.
                11. Provide your response directly without punctuation or introductory phrases.
                12. The title should have 8 WORDS MAXIMUM!
               ### Description:
               {message}"""
        })
    else:
        new_question.append({
            "role": "user",
            "content": f"""Your task is to generate the shortest possible title from the following description. 
                Instructions:
                1. Title Length: 7 to 8 words MAXIMUM.
                2. Content: Ensure the title capture the core idea of the description without extra details.
                3. Format: Provide the title as a single line, without any introductory phrases, extra text or ponctuation.
                
                Here is an example of how you should provide the title:
                - Original Description: "The RISK ANALYSIS of support systems shall consider MECHANICAL HAZARDS arising from static, dynamic, vibration, impact and pressure loading, foundation and other movements, temperature, environmental, manufacture and service conditions."
                - Rephrased Title: "Risk Analysis of Mechanical Hazards in Support Systems"
                
                REQUIREMENTS:
                4. Maximum 7 words.
                5. Response Format: Single line, only the title.
                6. Do not use quotation marks around your response.
                7. Provide your response directly without punctuation or introductory phrases.

                ### Description:
               {message}"""
        })

    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=new_question,
            temperature=0.5
        )
        content = response.choices[0].message.content
        return content
    except openai.APIConnectionError as e:
        raise (e, "The remote server is probably down...")


