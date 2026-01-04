import os
import json
import logging

class ActionManager:
    def __init__(self, filepath="all_actions.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.filepath = filepath
        self.actions = []
        self.discovered_actions = []

        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                try:
                    self.actions = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"File {self.filepath} is invalid, initialized empty list")
                    self.actions = []
        else:
            self.logger.warning(f"File {self.filepath} not found, initialized empty list")
            self.actions = []

    def update_actions(self, new_actions):
        for action in new_actions:
            if action not in self.actions:
                self.logger.info(f"New action detected: {action}")
            if action not in self.discovered_actions:
                self.discovered_actions.append(action)

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.actions, f, indent=4)
        self.logger.info(f"File {self.filepath} updated with {len(self.actions)} actions")

        discovered_path = os.path.splitext(self.filepath)[0] + "_discovered.json"
        existing = []
        if os.path.exists(discovered_path):
            try:
                with open(discovered_path, "r", encoding="utf-8") as f:
                    existing = json.load(f) or []
            except (json.JSONDecodeError, OSError):
                self.logger.warning(f"Unable to read {discovered_path}, initializing new list")

        new_elements = 0
        merged = list(existing)
        for a in self.discovered_actions:
            if a not in merged:
                merged.append(a)
                new_elements += 1

        with open(discovered_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=4)
        self.discovered_actions = merged
        self.logger.info(f"File {discovered_path} updated with {new_elements} discovered actions")
