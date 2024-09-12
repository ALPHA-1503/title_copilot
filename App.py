# Ensure all necessary imports are present
import os
import re
from typing import Tuple, Any, List, Dict, Union
from pathlib import Path

import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from polarion.workitem import Workitem
import scripts.file_helper as fh

from scripts.Polarion_connect import get_polarion_client_dev
from scripts.Polarion_connect import get_polarion_client_uat

from scripts.binary_handler import remove_saved_items, save_modified_items, get_saved_items, clear_saved_items
from scripts.polarion_comm import fetch_all_projects, fetch_project, update_work_item
from scripts.open_api_comm import send_message_to_mistral
load_dotenv()

# Initialize Polarion client and project group
polarion_client = get_polarion_client_dev()

# Initialize OpenAI client
api_client = OpenAI(base_url=os.environ.get("openai_api"), api_key="EMPTY")
iba_logo = Path(__file__).parent / "public" / "images" / "iba.png"
icon = Path(__file__).parent / "public" / "images" / "favicon.ico"


def validate_key(input_key: str) -> Tuple[gr.update, gr.update, gr.update]:
    """"
    This function is called when the user enters the key.
    It validates the key entered by the user.
    :param input_key: The key entered by the user
    :return: A tuple containing the message, the update for the dropdowns list of polarion projects & workitems's type.
    """
    if input_key == os.getenv("title_copilot_key"):
        gr.Info("Key validated", duration=3)
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
    else:
        gr.Warning("Warning Invalid Key !", duration=4)
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

def chatbot_response(message: str) -> str:
    return message

def on_cancel() -> gr.update:
    return gr.update(visible=False)

def on_project_selected(
        project_name: str,
        workitem_type: str
) -> Tuple[str, List[Workitem], List[Workitem], gr.update, gr.update, str]:
    """
    This function is called when a project is selected from the dropdown list.
    Calls start_working function to fetch the workitems from the selected project.
    :param project_name: The name of the selected project
    :param workitem_type:  The type of workitem to fetch
    :return: A tuple containing the message, the workitems, the saved items, the update for the ignore button, the update for the validate button and the project name
    """
    message, select_workitems, saved_items, visible_true, visible_false = start_working(project_name, workitem_type)
    return message, select_workitems, saved_items, visible_true, visible_false, project_name

def processed_workitem(item: Workitem, nb_workitem: int) -> str :
    messages = []
    messages.append(f"<strong>Remaining workitems :</strong> {nb_workitem} \n<br>🧩<strong>WORKITEM ID - [{item.id}]</strong>")
    return "\n".join(messages)

def handle_remove_items(saved_items: list, workitems: List[Workitem]) -> List[Workitem]:
    """
    This function is called when the user wants to continue from the saved work items.
    Calls the remove_saved_items function to remove the saved items from the workitems list.
    :param saved_items:  The saved work items
    :param workitems:  The work items fetched from the project
    :return: A tuple containing the message and the updated workitems list
    """
    workitems = remove_saved_items(workitems, saved_items)
    gr.Info("Removing modified items from the workitems list.", duration=10)
    return workitems

def start_working(
        project_name: str,
        workitem_type: str
) -> (
        Union[
            Tuple[str, Any, Any, Dict[str, Any], Dict[str, Any]],
        Tuple[str, List[Workitem], None, Any, Any],
        Tuple[str, None, None, Dict[str, Any], Dict[str, Any]],
        Tuple[str, List[Any], List[Any], List[Any], Dict[str, Any], Dict[str, Any]]
        ]
):
    """
    This function is called when a project is selected from the dropdown list.
    Calls the fetch_project function to get the selected project.
    Calls the get_saved_items function to get the saved work items.
    Calls the handle_mistral_chat function to handle the chat with the Mistral API.
    :param project_name: The name of the selected project
    :param workitem_type: The type of workitem to fetch
    :return:  A tuple containing the message, the workitems, the saved items, the update for the ignore button, the update for the validate button
    """
    project = fetch_project(project_name, polarion_client)
    if project:
        try:
            gr.Info(f"Searching workitems in {project_name}", duration=6)
            polarion_workitems = project.searchWorkitemFullItem(f'type:({workitem_type})', field_list=['id', 'description', 'title'])
            if polarion_workitems:
                saved_items = get_saved_items(project_name)
                if saved_items:
                    message = "Do you want to continue from the saved work items?" # Attend reponse YES/NO
                    return message, polarion_workitems, saved_items, gr.update(visible=True), gr.update(visible=False)
                else:
                    message, mistral_workitems, update1, update2, _, _, _ = handle_mistral_chat(polarion_workitems, False, [], False, project_name)
                    return message, mistral_workitems, None, update1, update2
            else:
                gr.Warning("No work items found.", duration=8)
                return "No work items found.", None, None, gr.update(visible=False), gr.update(visible=False)
        except EOFError as e:
            print("An error occurred: ", e)
            gr.Warning("An error occurred while fetching the workitems.", duration=2)
            return "An error occurred while fetching the workitems.", [],[],[], gr.update(visible=False), gr.update(visible=False)
    else:
        gr.Error("Failed to fetch project", duration=2)
        return f"Failed to fetch project {project_name}.", [],[],[], gr.update(visible=False), gr.update(visible=False)

def handle_mistral_chat(
        mistral_workitems: List[Workitem],
        is_retry: bool,
        history: list,
        clear_file: bool,
        project_name: str
) -> (
        Union[
            Tuple[str, List[Workitem], Dict[str, Any], Dict[str, Any], bool, Union[list, List[Tuple[Any, str]]], bool],
            Tuple[str, None, Dict[str, Any], Dict[str, Any], bool, list, bool]
        ]
):
    """
    This function is called when the user asked if he wants to load the saved items or not.
    Calls the clear_saved_items function to clear the saved items if the user wants to start from scratch.
    Calls the send_message_to_mistral function to send the message to the Mistral API.
    Replace the first item.title in the workitem object with the new title generated by Mistral.
    Calls the processed_workitem function to display the remaining workitems in the chat.
    Set the chatbot message with the original title, the original description and the new title generated by Mistral.
    :param mistral_workitems: The work items fetched from the project
    :param is_retry: A boolean to check if the user wants to retry the chat with Mistral
    :param history: A list to store the chat history
    :param clear_file: A boolean to check if the user wants to clear the saved items
    :param project_name: The name of the selected project
    :return: A tuple containing the message, the updated workitems list,
    the update for the ignore button, the update for the validate button,
    a boolean to check if the user wants to retry the chat,
    the chat history and a boolean to check if the user wants to clear the saved items
    """
    if clear_file:
        clear_saved_items(project_name)
        clear_file = False

    if mistral_workitems:
        number_of_workitems = len(mistral_workitems)
        item = mistral_workitems[0]
        original_title = mistral_workitems[0].title
        user_message = item.description.content
        if is_retry:
            reply = send_message_to_mistral(api_client, user_message, history, retry=True)
        else:
            reply = send_message_to_mistral(api_client, user_message, [], retry=False)
            history = []
        reply = re.sub(r'["\']', '', reply)
        mistral_workitems[0].title = reply                    # Update the workitem with the new title
        history.append((user_message, reply))
        initial_message = processed_workitem(item, number_of_workitems)
        message = f"""{initial_message}
        <br><br>
        <strong>Original title:  </strong> <p>{original_title}</p>
        <br>
        <strong>Original description:  </strong> <p>{item.description.content}</p>
        <br><strong>Proposition:  </strong> <p>{reply}</p>
        <br><strong>Do you want to validate this title?</strong>"""
        is_retry = False
        return message, mistral_workitems, gr.update(visible=False), gr.update(visible=True), is_retry, history, clear_file
    else:
        gr.Warning("No work items found.", duration=5)
        return "No work items found.", None, gr.update(visible=False), gr.update(visible=False), is_retry, history, clear_file

def validate(
        validate_workitems: List[Workitem],
        history: list,
        button: str,
        project_name: str
) -> Tuple[str, List[Workitem], gr.update, gr.update]:
    """
    This function is called when the user clicks on the YES, NO or SKIP button.
    This function checks if the pressed button is YES, NO or SKIP.
    It takes the first work item from the list and updates it in the database.
    :param validate_workitems: The work items fetched from the project
    :param history: A list to store the chat history
    :param button: The button pressed by the user
    :param project_name: The name of the selected project
    :return: A tuple containing the message, the updated workitems list, the update for the ignore button and the update for the validate button
    """
    if button == "YES":
        if validate_workitems:
            current_item = validate_workitems.pop(0)
            gr.Info(f"Updated WorkItem: {current_item.id}", duration=2)
            current_item.title = re.sub(r'["\']', '', current_item.title)
            update_work_item(polarion_client, current_item.title, current_item.id, project_name)  # Update the item in the database
            save_modified_items(current_item.id, project_name)
            next_message, validate_workitems, row_ignore_saved_items, row_validate_title, _, _, _ = handle_mistral_chat(validate_workitems, False, history, False, project_name)
            return f"{next_message}", validate_workitems, row_ignore_saved_items, row_validate_title
        else:
            gr.Warning("No more work items to process!", duration=2)
            return "No more work items to process.", validate_workitems, gr.update(visible=False), gr.update(visible=True)
    elif button == "NO":
        gr.Info(f"Retrying", duration=2)
        message, validate_workitems, row_ignore_saved_items, row_validate_title, is_retry, history, clear_file = handle_mistral_chat(validate_workitems, True, history, False, project_name)
        return message, validate_workitems, gr.update(visible=False), gr.update(visible=True)
    elif button == "SKIP":
        validate_workitems.pop(0)
        message, validate_workitems, _, _, _, _, _ = handle_mistral_chat(validate_workitems, False, history, False, project_name)
        return message, validate_workitems, gr.update(visible=False), gr.update(visible=True)


def start_edit():
    return  gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

def on_edit(
        new_title: str,
        edit_workitems: List[Workitem],
        history: list, project_name: str
) -> Tuple[gr.update, gr.update, str, List[Workitem], gr.update, gr.update]:
    """
    This function is called when the user wants to edit the generated title.
    This function check if there is a new title entered by the user. If yes, it updates the work item in the database.
    :param new_title: The new title entered by the user
    :param edit_workitems: The work items fetched from the project
    :param history: A list to store the chat history
    :param project_name: The name of the selected project
    :return:
    """
    if new_title:
        current_item = edit_workitems.pop(0)
        gr.Info(f"Updated WorkItem: {current_item.id}", duration=2)
        update_work_item(polarion_client, new_title, current_item.id, project_name)  # Update the item in the database
        save_modified_items(current_item.id, project_name)
        next_message, validate_workitems, row_ignore_saved_items, row_validate_title, _, _, _ = handle_mistral_chat(edit_workitems, False, history, False, project_name)
    return gr.update(visible=False), gr.update(visible=True), f"{next_message}", validate_workitems, row_ignore_saved_items, row_validate_title


def close_edit():
    return gr.update(visible=False), gr.update(visible=True)

with gr.Blocks(title="Polarion Copilot - Title generator", fill_height=True, fill_width=True) as demo:
    with gr.Row():
        title = gr.HTML(elem_id="header",
                        value=f"""
                        <div id="gradio_header">
                            <img id="logo" src='file/{iba_logo}' alt="IBA Logo">
                            <h1>Welcome to Title Copilot !</h1>
                        </div>
                        """
                        )

    with gr.Row() as selects_row :
        key_input = gr.Textbox(label="Enter your key", lines=1, type="password")
        project_ids = fetch_all_projects(polarion_client, 'Therapy_Center_Spec')
        workitem_type = [("🟪 Normative Requirement","normativeRequirement"), ("🟪 Requirement","requirement"), ("🟦 Definition","definition"), ("⚠️ Test case","test"), ("⚠️ Verification by analysis","verificationbyanalysis"),("⚠️ Verification test case","verificationtestcase"), ("🛡️ Safety decision","safetydecision"),("⚠️ Automated test case","automatedtestcase"),("⚡ Failure mode","failuremode"),("❓ Hazard","hazard"),("🟦 User requirement","userrequirement")  ]
        type_dropdown = gr.Dropdown(workitem_type, label="Select a workitem type",interactive=True, visible=False)
        dropdown = gr.Dropdown(project_ids, label="Select a project from Polarion", interactive=True, visible=False)


    with gr.Row():
        main_window = gr.HTML(label="MISTRAL", elem_id="main_window")


    with gr.Row(visible=False) as row_ignore_saved_items:
        yes_button_saved_items = gr.Button("YES ✅", elem_id="yes_button_ignore")
        no_button_saved_items = gr.Button("NO ❌", elem_id="no_button_ignore")

    with gr.Row(visible=False) as row_validate_title:
        yes_button_validate = gr.Button("YES ✅", elem_id="yes_button_validate")
        edit_button_validate = gr.Button("EDIT 📝", elem_id="edit_button_validate")
        no_button_validate = gr.Button("NO ❌", elem_id="no_button_validate")
        skip_button_validate = gr.Button("SKIP", elem_id="skip_button_validate")

    with gr.Row(visible=False) as row_continue_saved_items:
        yes_button_continue = gr.Button("YES ✅", elem_id="yes_button_continue")
        no_button_continue = gr.Button("NO ❌", elem_id="no_button_continue")

    with gr.Row(visible=False) as edit_row:
        with gr.Column(scale=4):
            chatbox = gr.Textbox(label="Editing generated title", lines=1)
        with gr.Column(scale=1):
            save_button = gr.Button("SAVE 💾", elem_id="save_button")
            cancel_button = gr.Button("CANCEL ❌", elem_id="cancel_button")


    demo.css = fh.get_css(Path(__file__).parent / "public" / "styles" / "gradio.css")

    project_name = gr.State()
    saved_items = gr.State()
    workitems = gr.State()
    history = gr.State([])
    user_message = gr.State()
    is_retry = gr.State()
    clear_file = gr.State()

    key_input.submit(
        validate_key,
        inputs=[key_input],
        outputs=[key_input, type_dropdown, dropdown]
    )

    dropdown.change(
        on_project_selected,
            inputs=[dropdown, type_dropdown],
            outputs=[main_window, workitems, saved_items, row_ignore_saved_items, row_validate_title, project_name]
    )

    yes_button_saved_items.click(
        lambda saved_items, workitems, is_retry, history:
            handle_mistral_chat(handle_remove_items(saved_items, workitems), is_retry, history, clear_file, project_name),
                inputs=[saved_items, workitems, is_retry, history],
                outputs=[main_window, workitems, row_ignore_saved_items, row_validate_title, is_retry, history, clear_file]
    )

    no_button_saved_items.click(
        handle_mistral_chat,
            inputs=[workitems, is_retry, history, gr.State(True), project_name],
            outputs=[main_window, workitems, row_ignore_saved_items, row_validate_title, is_retry, history, clear_file]
    )

    yes_button_validate.click(
        validate,
            inputs=[workitems, history, gr.State("YES"), project_name],
            outputs=[main_window, workitems, row_ignore_saved_items, row_validate_title]
    )

    no_button_validate.click(
        validate,
            inputs=[workitems, history, gr.State("NO"), project_name],
            outputs=[main_window, workitems, row_ignore_saved_items, row_validate_title]
    )

    skip_button_validate.click(
        validate,
        inputs=[workitems, history, gr.State("SKIP"), project_name],
        outputs=[main_window, workitems, row_ignore_saved_items, row_validate_title]
    )

    edit_button_validate.click(     # IMPROVEMENT --> Set the chatbox with the actual title for a better user experience - Van Eenoo Arnaud.
        start_edit,
            inputs=[], #
            outputs=[row_ignore_saved_items, row_validate_title, edit_row]
    )

    cancel_button.click(
        close_edit,
            inputs=[],
            outputs=[edit_row, row_validate_title],
    )

    save_button.click(
        on_edit,
            inputs=[chatbox, workitems, history, project_name],
            outputs=[edit_row, row_validate_title, main_window, workitems, row_ignore_saved_items, row_validate_title]
    )

    chatbox.submit(chatbot_response, chatbox, main_window)



if __name__ == "__main__":
    demo.launch(favicon_path=icon.__str__(), show_error=True, allowed_paths=["."], server_name="127.0.0.1", server_port=7861, root_path="/title-copilot")