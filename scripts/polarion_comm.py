# Function to get all projects
from polarion.polarion import Polarion


def fetch_all_projects(client_polarion, location: str) -> list:
    try:
        projects = client_polarion.getRepoProjects(location)
        project_list = [project.id for project in projects]
        project_list.sort()
        return project_list
    except Exception as e:
        print(f"Error: {e}")
        return []

# Function to fetch a project
def fetch_project(project_name: str, polarion_client: Polarion):
    try:
        return polarion_client.getProject(project_name)
    except Exception as e:
        print(f"Error: {e}")

# Function to update a work item in Polarion
def update_work_item(polarion_client, new_title: str, work_item_id: str, project_name: str) -> None:
    try:
        project = polarion_client.getProject(project_name)
        workitem = project.getWorkitem(work_item_id)
        workitem.title = new_title
        workitem.save()
    except Exception as e:
        raise Exception('An error occurred : ', e)