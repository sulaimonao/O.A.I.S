# agents/agent.py

class Agent:
    def __init__(self):
        self.interface = AgentInterface()

    def perform_task(self, user_input):
        action_plan = self.interface.interpret_task(user_input)
        print(f"Action Plan: {action_plan}")
        result = self.interface.execute_action(action_plan)
        return result
