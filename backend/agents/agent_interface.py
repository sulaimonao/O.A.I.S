# agents/agent_interface.py

from models.gpt2_agent import GPT2AgentModel

class AgentInterface:
    def __init__(self):
        self.model = GPT2AgentModel()

    def interpret_task(self, user_input):
        prompt = f"Task: {user_input}\nAction Plan:"
        action_plan = self.model.generate_text(prompt)
        return action_plan

    # agents/agent_interface.py (continued)

    def execute_action(self, action_plan):
        # Simplified parsing logic
        if "read file" in action_plan.lower():
            file_path = self.extract_file_path(action_plan)
            from tools.file_operations import read_file
            content = read_file(file_path)
            return content
        elif "list directory" in action_plan.lower():
            from tools.os_helpers import list_directory
            files = list_directory()
            return files
        else:
            return "Action not recognized."

    def extract_file_path(self, action_plan):
        # Implement logic to extract file path from action plan
        return 'path_to_file'

