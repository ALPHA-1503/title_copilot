import os, re, html
from openai import OpenAI
from dotenv import load_dotenv
from scripts.Polarion_connect import get_polarion_client_dev
from scripts.polarion_comm import fetch_project
from scripts.open_api_comm import send_message_to_mistral
from scripts.binary_handler import get_saved_items, save_modified_items, clear_saved_items

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
api_client = OpenAI(api_key=api_key, base_url=os.environ.get("OPENAI_API"))

polarion_client = get_polarion_client_dev()
load_dotenv()

def ask(question: str) -> bool:
    while True:
        answer = input (f"{question} (y/n) : ").strip().lower()
        while not answer in ['y', 'n']:
            print("Please answer with 'y' (yes) or 'n' (no).")
        if answer == 'y':
            return True
        else:
            return False

def clear_screen():
    #windows
    if os.name == 'nt':
        try:
            os.system('cls')
        except EOFError as e:
            print('An error occurred : ',e)
        #linux
    else:
        try:
            os.system('clear')
        except EOFError as e:
            print('An error occurred : ', e)

def get_project_name() -> str:
    name = ""
    while not name.strip():
        name = input('Enter the project name (ex: PT_Regulations_And_Standards) : ')
        if not name.strip():
            print("Project name cannot be empty. Please try again.")
    return name


def process_workitem(item, history, nb_workitem, total_workitems,project_name):
    workitemsID = []
    validate = False
    clear_screen()
    print(f"\nWorkitem N° {nb_workitem}/{total_workitems} - ID [{item.id}]")
    user_message = item.description.content
    reply = send_message_to_mistral(api_client, user_message, history, retry=False)
    print(f"\nOriginal title:", item.title)
    description = html.unescape(item.description.content)
    description = re.sub(r'<[^>]*>', '', description)
    print(f"Original description:", description)
    print(f"\nNew title:", reply)

    while not validate:
        yes = ask(f"Does that suit you?")
        if not yes:
            clear_screen()
            print(f"\nWorkitem N° {nb_workitem}/{total_workitems} - ID [{item.id}]")
            history.append([user_message, reply])  # Log the failed attempt
            reply = send_message_to_mistral(api_client, user_message, history, retry=True)
            print(f"\nOriginal title :     ", item.title)
            description = html.unescape(item.description.content)
            description = re.sub(r'<[^>]*>', '', description)
            print(f"Original description :", description)
            print(f"\nNew title :", reply)
        else:
            print(f"Row updated!")
            validate = True
            workitemsID.append(item.id)
            save_modified_items(workitemsID, project_name)

        #update_work_item(polarion_client, reply, item.id)


def check_saved_items(workitems, project_name):
    saved_items = get_saved_items(project_name)
    if saved_items:
        if ask("\nSaved items found. Do you want to continue from where you left off?"):
            for item in saved_items:
                for workitem in workitems:
                    if workitem.id == item:
                        workitems.remove(workitem)
            return workitems
        else:
            clear_saved_items(project_name)
    else:
        return False

if __name__ == "__main__":
    clear_screen()
    history = []
    print('--- Welcome to Title Copilot! ---\n')
    while True:
        project_name = get_project_name()
        project = fetch_project(project_name, polarion_client)
        workitems = project.searchWorkitemFullItem('type:normativeRequirement',field_list=['id', 'description', 'title'], limit=100)
        saved_items = check_saved_items(workitems,project_name)
        total_workitems = len(workitems)
        for nb_workitem, item in enumerate(workitems):
            process_workitem(item, history, nb_workitem, total_workitems, project_name)