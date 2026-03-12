from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import re

@dataclass
class InfoPool:
    """Keeping track of all information across the agents."""
    
    # User input / accumulated knowledge
    instruction: str = ""
    task_name: str = ""
    additional_knowledge_manager: str = ""
    additional_knowledge_executor: str = ""
    add_info_token = "[add_info]"
    
    ui_elements_list_before: str = "" # List of UI elements with index
    ui_elements_list_after: str = "" # List of UI elements with index
    action_pool: list = field(default_factory=list)

    # Working memory
    summary_history: list = field(default_factory=list)  # List of action descriptions
    action_history: list = field(default_factory=list)  # List of actions
    action_outcomes: list = field(default_factory=list)  # List of action outcomes
    error_descriptions: list = field(default_factory=list)

    last_summary: str = ""  # Last action description
    last_action: str = ""  # Last action
    last_action_thought: str = ""  # Last action thought
    important_notes: str = ""
    
    error_flag_plan: bool = False # if an error is not solved for multiple attempts with the executor
    error_description_plan: bool = False # explanation of the error for modifying the plan

    # Planning
    plan: str = ""
    completed_plan: str = ""
    progress_status: str = ""
    progress_status_history: list = field(default_factory=list)
    finish_thought: str = ""
    current_subgoal: str = ""
    err_to_manager_thresh: int = 2

    # future tasks
    future_tasks: list = field(default_factory=list)

class BaseAgent(ABC):
    @abstractmethod
    def get_prompt(self, info_pool: InfoPool) -> str:
        pass
    @abstractmethod
    def parse_response(self, response: str) -> dict:
        pass

class Manager(BaseAgent):
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "You are an agent who can operate an Android phone on behalf of a user. Your goal is to track progress and devise high-level plans to achieve the user's requests.\n\n"
        prompt += "### User Request ###\n"
        prompt += f"{info_pool.instruction}\n\n"

        if info_pool.plan == "":
            prompt += "---\n"
            prompt += "Make a high-level plan to achieve the user's request. If the request is complex, break it down into subgoals.\n"
            prompt += "IMPORTANT: For requests that explicitly require an answer, always add 'perform the `answer` action' as the last step to the plan!\n\n"
            prompt += "### Guidelines ###\n"
            if info_pool.additional_knowledge_manager != "":
                prompt += f"{info_pool.additional_knowledge_manager}\n\n"
            prompt += "Provide your output in the following format:\n### Thought ###\nRationale...\n\n### Plan ###\n1. subgoal...\n"
        else:
            prompt += f"### Historical Operations ###\n{info_pool.completed_plan}\n\n"
            prompt += f"### Plan ###\n{info_pool.plan}\n\n"
            prompt += f"### Last Action ###\n{info_pool.last_action}\n\n"
            prompt += f"### Last Action Description ###\n{info_pool.last_summary}\n\n"
            if info_pool.error_flag_plan:
                prompt += "### Potentially Stuck! ###\n"
            prompt += "Update the plan based on current status.\n"
        return prompt

    def parse_response(self, response: str) -> dict:
        thought = ""
        completed_subgoal = "No completed subgoal."
        plan = ""
        if "### Thought" in response:
            thought = response.split("### Thought")[-1].split("###")[0].strip()
        if "### Historical Operations" in response:
            completed_subgoal = response.split("### Historical Operations")[-1].split("###")[0].strip()
        if "### Plan" in response:
            plan = response.split("### Plan")[-1].strip()
        return {"thought": thought, "completed_subgoal": completed_subgoal, "plan": plan}

ANSWER = "answer"
CLICK = "click"
LONG_PRESS = "long_press"
TYPE = "type"
SYSTEM_BUTTON = "system_button"
SWIPE = "swipe"

ATOMIC_ACTION_SIGNITURES = {
    ANSWER: {"arguments": ["text"]},
    CLICK: {"arguments": ["coordinate"]},
    LONG_PRESS: {"arguments": ["coordinate"]},
    TYPE: {"arguments": ["text"]},
    SYSTEM_BUTTON: {"arguments": ["button"]},
    SWIPE: {"arguments": ["coordinate", "coordinate2"]}
}

class Executor(BaseAgent):
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "Decide the next action.\n"
        prompt += f"### User Request ###\n{info_pool.instruction}\n\n"
        prompt += f"### Overall Plan ###\n{info_pool.plan}\n\n"
        prompt += "### Atomic Actions ###\n"
        for action, value in ATOMIC_ACTION_SIGNITURES.items():
            prompt += f"- {action}({', '.join(value['arguments'])})\n"
        return prompt

    def parse_response(self, response: str) -> dict:
        thought = ""
        action = ""
        description = ""
        if "### Thought" in response:
            thought = response.split("### Thought")[-1].split("###")[0].strip()
        if "### Action" in response:
            action = response.split("### Action")[-1].split("###")[0].strip()
        if "### Description" in response:
            description = response.split("### Description")[-1].strip()
        return {"thought": thought, "action": action, "description": description}

class ActionReflector(BaseAgent):
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "Verify the last action.\n"
        prompt += f"Action: {info_pool.last_action}\nExpectation: {info_pool.last_summary}\n"
        return prompt

    def parse_response(self, response: str) -> dict:
        outcome = "A"
        error_description = "None"
        if "### Outcome" in response:
            outcome = response.split("### Outcome")[-1].split("###")[0].strip()
        if "### Error Description" in response:
            error_description = response.split("### Error Description")[-1].strip()
        return {"outcome": outcome, "error_description": error_description}

class Notetaker(BaseAgent):
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "Take notes of important content.\n"
        return prompt

    def parse_response(self, response: str) -> dict:
        important_notes = ""
        if "### Important Notes" in response:
            important_notes = response.split("### Important Notes")[-1].strip()
        return {"important_notes": important_notes}