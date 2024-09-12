import pickle
import os
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"
secret_path = Path(__file__).parent / "certif" / "key.pkl"

# Function to load saved items
def remove_saved_items(workitems: list, saved_items: list):
    try:
        for item in saved_items:
            for workitem in workitems:
                if workitem.id == item:
                    workitems.remove(workitem)
        return workitems
    except EOFError as e:
        print("An error occurred : ",e)
        return []

def save_modified_items(workitems_id: list, project_name: str):
    file_path = data_dir / f"{project_name}.pkl"
    if os.path.exists(file_path):
        try:
            with open(str(file_path), 'rb') as f:
                existing_data = pickle.load(f)
        except EOFError:
            existing_data = []
    else:
        existing_data = []
    existing_data.append(workitems_id)

    try:
        with open(str(file_path), 'wb') as f:
            pickle.dump(existing_data, f)
    except Exception as e:
        print("An error occurred : ", e)

# Function to get saved items
def get_saved_items(project_name: str):
    file_path = data_dir / f"{project_name}.pkl"
    if os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except EOFError as e:
            print("An error occurred : ", e)
            return []
    else:
        return []

def clear_saved_items(project_name: str):
    file_path = data_dir / f"{project_name}.pkl"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print("Saved items cleared.")
        except Exception as e:
            print("An error occurred : ", e)
    else:
        print("No saved items found.")