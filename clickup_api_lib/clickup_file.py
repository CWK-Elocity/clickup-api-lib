import requests
from datetime import datetime

def is_not_empty(value):
    if value is None:
        return False
    if isinstance(value, float) and value != value:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return False
    return True

class Clickup:
    def __init__(self, api_token, name=None, list_id=None):
        """creates an instance of Clickup task

        Args:
            list_id (int): Id of list in which the task will be added
            api_token (int): api_token id used to connect to clickup api
            name (str): Name of the task
        """
        self.base_url = "https://api.clickup.com/api/v2/"
        self.headers = {
            "Authorization": api_token
        }
        self.body = {}
        self.add_name(name)
        self.id = None
        self.valid_CustomFields_ids = None
        self.list_id = list_id
        self.customFields = []

    def check_task_validity(self, task_id=None):
        """Checks if task is valid and exists

        Args:
            task_id (int): Id of task

        Raises:
            ValueError: for Unexpected errors

        Returns:
            Boolean: If valid - True if not valid - 
        """
        if task_id is None:
            if self.id is None:
                raise ValueError("No task to check. No ID given.")
            else:
                url = f"{self.base_url}task/{self.id}"
        else:
            url = f"{self.base_url}task/{task_id}"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            raise ValueError(f"Unexpected error occurred: {e}")

    def get_tasks(self, list_id):
        """Obtains a task

        Args:
            list_id (int): id of list that tasks will be obtained from

        Returns:
            object: an JSON object with task metadata
        """
        url = f"{self.base_url}list/{list_id}/task"
        try:
            response = requests.get(url, headers=self.headers)
        except Exception as e:
            raise ValueError(f"Could not obtain tasks: {e}")
        return response.json()
    
    def get_list_id(self, space_id, list_name, folder_id=None):
        """Obtains a list id

        Args:
            space_id (int): ID of space in wich the wanted list is. If it is an list inside folder it can be anything.
            list_name (str): Name of the wanted list
            folder_id (str, optional): If it's folderless list leave it blank. Defaults to None.

        Raises:
            ValueError: If api resposed with error
            ValueError: If there is no list of that name in folderless list
            ValueError: If there is no list of that name in list inside a folder

        Returns:
            str: id of that list
        """
        if folder_id is None:
            url = f"{self.base_url}space/{space_id}/list"
        else:
            # Get lists within the folder
            url = f"{self.base_url}folder/{folder_id}/list"

        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            lists = response.json()["lists"]
            for lista in lists:
                if lista["name"] == list_name:
                    return lista["id"]
        else:
            raise ValueError("Could not obtain api response")
        
        if folder_id is None:
            raise ValueError(f"There is no list of that name: {list_name} in that space: {space_id}")
        else:
            raise ValueError(f"There is no list of that name: {list_name} in that folder id: {folder_id}")
        
    def add_task(self, list_id = None):
        """Adds a task if not already added with all data gather with other methods

        Args:
            list_id (int): Redefines or defines list id if was not defined earlier.

        Raises:
            ValueError: If for some reason task could not be created
            ValueError: If task was already created
        """
        if list_id is not None:
            self.list_id = list_id

        if self.list_id is None:
            raise ValueError("None list id provided.")
        
        if self.id is not None:
            raise ValueError("Task already created.")
        
        if 'name' not in self.body or not is_not_empty(self.body['name']):
            raise ValueError("Task creation failed: 'name' is missing or empty in the task body.")

        
        url = f"{self.base_url}list/{self.list_id}/task"
        try:
            response = requests.post(url=url, headers=self.headers, json=self.body)

            if response.status_code == 200:
                self.id = response.json().get("id")
                if not self.id:
                    raise ValueError("Task creation failed: 'id' not found in response.")
            else:
                raise ValueError(f"Task creation failed: {response.status_code} {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Unexcpeted error occurred while adding task: {e}")

    def add_description(self, description):
        """Adding description to a task body

        Args:
            description (str): A description of the task

        Raises:
            ValueError: If description is not a string
        """
        if isinstance(description, str):
            self.body["description"] = description
        else:
            raise ValueError("Description must be a string")
        
    def add_markdown_description(self, markdown_description):
        """Adding description in markdown to a task body

        Args:
            description (str): A markdown description of the task

        Raises:
            ValueError: If description is not a string
        """
        if isinstance(markdown_description, str):
            self.body["markdown_description"] = markdown_description
        else:
            raise ValueError("Markdown description must be a string")

    def add_assignees(self, assignees):
        """Adds assignees to a task body

        Args:
            assignees (list): List of assginees id's or just one id

        Raises:
            ValueError: If assignees is not a list or one item
            ValueError: If one of the assignees is not an integer
        """
        if isinstance(assignees, int):
            assignees = [assignees]
        elif isinstance(assignees, (set, tuple)):
            assignees = list(assignees)
        elif not isinstance(assignees, list):
            raise ValueError("Assignees must be a list or one item")

        for assignee in assignees:
            if not isinstance(assignee, int):
                raise ValueError("All assignees must be an integers")
            
        self.body["assignees"] = assignees

    def add_tags(self, tags):
        """Adds tags to a task body

        Args:
            tags (list): List of tags that task will have

        Raises:
            ValueError: If give tags are not valid type
        """
        if isinstance(tags, str):
            tags = [tags]
        elif isinstance(tags, (set, tuple)):
            tags = list(tags)
        elif not isinstance(tags, list):
            raise ValueError("Assignees must be a list or one item")
        
        tags = [str(tag) for tag in tags]
                
        self.body["tags"] = tags
    
    def add_status(self, status):
        """Adds status to a task body

        Args:
            status (str): A valid status name. It's important that this is valid, cuz if not task will not be added
            valid_statuses (list): List of valid statuses. Can be left empty.

        Raises:
            ValueError: If after str() status is still not string
        """
        if not hasattr(self, 'validStatuses') or not self.validStatuses:
            self.get_statuses()
            if not hasattr(self, 'validStatuses') or not self.validStatuses:
                raise ValueError("Could not obtain statuses. No list ID provided.")
    

        try:
            status = str(status)
        except Exception:
            raise ValueError(f"Status {status} could not be converted to a string")
        
        """ obsolete
        if valid_statuses is not None:
            valid_statuses = list(valid_statuses)
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}. Valid statuses are: {valid_statuses}")
        """

        if status not in self.validStatuses.values():   
            raise ValueError(f"Invalid status: {status}. Valid statuses are: {self.validStatuses.values()}")
        
        self.body["status"] = status

    def add_priority(self, priority, valid_priorities=None):
        """Adds a priority to a task body

        Args:
            priority (int): Priority of the task
            valid_priorities (list): List of valid priorities. can be left empty.

        Raises:
            ValueError: Invalid priority that is not in valid_priorities
            ValueError: If after conversion priority is still not a int
        """
        try:
            priority = int(priority)
        except Exception:
            raise ValueError(f"Priority {priority} could not be converted into an integer")
        
        if valid_priorities is not None:
            valid_priorities = list(valid_priorities)
            if priority not in valid_priorities:
                raise ValueError(f"Invalid priority: {priority}. Valid priorities are: {valid_priorities}")
        
        self.body["priority"] = priority
    
    def add_dueDate(self, time, specify_time=False):
        """Adds a due date to task body

        Args:
            time (int): Time in unix aproach (millis)
            specify_time (bool, optional): If you want due time to have exact hour and minute. Defaults to False.

        Raises:
            ValueError: If duedate was earlier than now
        """
        due_date = datetime.fromtimestamp(time/1000)
        current_time = datetime.now()
        if due_date <= current_time:
            raise ValueError(f"Due date {due_date} must be in the future")
        self.body["due_date"] = time
        self.body["due_date_time"] = specify_time

    
    def add_timeEstimation(self, time):
        """Adds a time estimated for task doing.

        Args:
            time (int): Time in unix aproach (millis)
        """
        self.body["time_estimate"] = time
    
    def add_startDate(self, time, specify_time=False):
        """Adds a start date to task body

        Args:
            time (int): Time in unix aproach (millis)
            specify_time (bool, optional): If you want stary time to have exact hour and minute. Defaults to False.

        Raises:
            ValueError: If start date was earlier than previous day
        """
        start_date = datetime.fromtimestamp(time/1000)
        current_time = datetime.now()
        if start_date < current_time and (current_time - start_date) > 1:
            raise ValueError(f"Start date {start_date} must be in max one day in the past")
        self.body["start_date"] = time
        self.body["start_date_time"] = specify_time
        
    def add_notifyAll(self, notify):
        """If you want to notify all

        Args:
            notify (boolean): true/false

        Raises:
            ValueError: if notify was not boolean
        """
        if isinstance(notify, bool):
            self.body["notify_all"] = notify
        else:
            raise ValueError("Argument was not a boolean")
        
    def add_parent(self, task_id):
        """Adds a parent task to a task

        Args:
            task_id (int): ID of parent task

        Raises:
            ValueError: If parent task wasn't found in tasks.
        """
        if isinstance(task_id, str):
            valid = self.check_task_validity(task_id)
            if valid:
                self.body["parent"] = task_id
            else:
                raise ValueError(f"Invalid task ID: {task_id}")
        
    def add_linksTo(self, task_id):
        """Adds a link task to a task

        Args:
            task_id (int): ID of linked task

        Raises:
            ValueError: If linked task wasn't found in tasks.
        """
        if isinstance(task_id, int):
            valid = self.check_task_validity(task_id)
            if valid:
                self.body["links_to"] = task_id
            else:
                raise ValueError(f"Invalid task ID: {task_id}")

    def add_customFields(self, customFields):
        """Adds custom fields to a task

        Args:
            customFields (dict): a dictionary with customfields

        Raises:
            ValueError: If given customFields weren't a dict
            ValueError: If customField wasn't found in the list
            ValueError: If one cusotmFields value was not a string 
        """
        if not isinstance(customFields, dict):
            raise ValueError(f"Expected a dict instance from customFields")
        
        if self.valid_CustomFields_ids is None:
            self.valid_CustomFields_ids = [field["id"] for field in self.get_customFields()["fields"]]

        for key, value in customFields.items():
            if key not in self.valid_CustomFields_ids:
                raise ValueError(f"Invalid custom field ID: {key}")
            
            if isinstance(value, str):
                self.customFields.append({"id": key, "value": value})
            else:
                raise ValueError(f"Invalid custom field value for {key}: {value}")

        self.body["custom_fields"] = self.customFields

    def get_customFields(self):
        """Gets a valid customFields from list

        Raises:
            ValueError: If failed in fetching custom fields

        Returns:
            JSON: whole answer of the server
        """
        url = f"{self.base_url}list/{self.list_id}/field"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch custom fields: {e}")

    def add_watcher(self, user_id):
        if not hasattr(self, 'body') or not isinstance(self.body, dict):
            self.body = {}

        if "watchers" not in self.body:
            self.body["watchers"] = {"add": [], "rem": []}

        if user_id not in self.body["watchers"]["add"]:
            self.body["watchers"]["add"].append(user_id)

    def remove_watcher(self, user_id):
        if not hasattr(self, 'body') or not isinstance(self.body, dict):
            self.body = {}

        if "watchers" not in self.body:
            self.body["watchers"] = {"add": [], "rem": []}

        if user_id not in self.body["watchers"]["rem"]:
            self.body["watchers"]["rem"].append(user_id)


    def add_name(self, name):
        """Adds task name 

        Args:
            name (string): task name

        Raises:
            ValueError: if name was not string
        """
        
        if isinstance(name, str):
            self.body["name"] = name
        else: 
            try:
                name = str(name)
            except Exception:
                raise ValueError("Name could not be converted to a string")
        
    def get_customFieldId(self, name):
        self.CustomField_id = next([field["id"] for field in self.get_customFields().get("fields", []) if field["name"] == name], None)
        return self.CustomField_id

    def clear_task(self):
        self.body = {
            }
        self.customFields = []

    def update_task(self):
        """Update task  

        Raises:
            ValueError: If task was already created
        """
        
        if self.id is None:
            raise ValueError("No task ID provided.")
        
        url = f"{self.base_url}task/{self.id}"
        try:
            response = requests.put(url=url, headers=self.headers, json=self.body)

            if response.status_code == 200:
                return response.json()

            else:
                raise ValueError(f"Task update failed: {response.status_code} {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Unexcpeted error occurred while updateing task: {e}")
        
    def get_statuses(self):
        """Obtains a list of statuses

        Args:
            list_id (int): id of list that statuses will be obtained from

        Returns:
            object: an JSON object with task metadata
        """
        if self.list_id is None:
            raise ValueError("No list ID provided.")
        url = f"{self.base_url}list/{self.list_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                pass
            else:
                raise ValueError(f"Failed to fetch statuses: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch statuses: {e}")
        statuses = {}
        try:
            for status in response.json()["statuses"]:
                if not isinstance(status["status"], str):
                    raise ValueError(f"Status {status['status']} is not a string")
                orderindex = status["orderindex"]
                status_str = status["status"]
                statuses[orderindex] = status_str
                self.validStatuses = statuses
        except KeyError as e:
            raise ValueError(f"Failed to parse statuses from response: {e}.")

    def get_first_status(self):
        """Obtains the first status from the list

        Returns:
            str: name of the first status
        """
        if hasattr(self, 'validStatuses') and self.validStatuses:
            statuses = self.validStatuses
        else:
            self.get_statuses()
            if not hasattr(self, 'validStatuses') or not self.validStatuses:
                raise ValueError("Could not obtain statuses. No list ID provided.")
            statuses = self.validStatuses
        if statuses:
            return statuses[0]
        else:
            raise ValueError("No statuses found in the list.")
        
    def get_space_id(self):
        """Obtains the space id from the list id

        Returns:
            str: id of the space
        """
        if self.list_id is None:
            if self.id is None:
                raise ValueError("No list ID nor task id provided.")
            else:
                url = f"{self.base_url}task/{self.id}"
                try:
                    response = requests.get(url, headers=self.headers)
                    if response.status_code == 200:
                        self.list_id = response.json().get("list", {}).get("id")
                    else:
                        raise ValueError(f"Failed to fetch list ID from task: {response.status_code} {response.text}")
                except requests.exceptions.RequestException as e:
                    raise ValueError(f"Failed to fetch list ID from task: {e}")
        
        url = f"{self.base_url}list/{self.list_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                self.space_id = response.json().get("space", {}).get("id")
                return response.json().get("space", {}).get("id")
            else:
                raise ValueError(f"Failed to fetch space ID: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch space ID: {e}")
        
    def get_space_tags(self):
        """Obtains the tags from the space

        Returns:
            list: list of tags
        """
        if not hasattr(self, 'space_id') or not self.space_id:
            self.get_space_id()
        space_id = self.space_id
        url = f"{self.base_url}space/{space_id}/tag"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                self.tags = response.json().get("tags", [])
                return response.json().get("tags", [])
            else:
                raise ValueError(f"Failed to fetch tags: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch tags: {e}")
        
    def add_tag(self, tag_name):
        """Adds a tag to the task

        Args:
            tag_name (str): name of the tag to be added

        Raises:
            ValueError: If tag name is not a string
        """
        if not hasattr(self, 'tags') or not self.tags:
            self.get_space_tags()
        
        if isinstance(tag_name, str):
            if "tags" not in self.body:
                self.body["tags"] = []
            self.body["tags"].append(tag_name)
        else:
            raise ValueError("Tag name must be a string")
        
    def add_attachment(self, file_stream, filename="attachment"):
        """Adds an attachment (file stream) to the task via ClickUp API

        Args:
            file_stream (file-like object): File opened in binary mode or io.BytesIO
            filename (str): Name for the uploaded file

        Raises:
            ValueError: If file_stream is not file-like or task ID is not set
        """
        if not hasattr(file_stream, "read"):
            raise ValueError("file_stream must be a file-like object (e.g., open('file', 'rb') or io.BytesIO)")
        if not self.id:
            raise ValueError("Task ID is not set. Create the task first.")

        url = f"{self.base_url}task/{self.id}/attachment"
        headers = {
            "Authorization": self.headers["Authorization"]
        }
        files = {"attachment": (filename, file_stream)}
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to upload attachment: {response.status_code} {response.text}")