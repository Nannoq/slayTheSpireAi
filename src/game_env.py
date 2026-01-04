import time
import logging
from gymnasium import spaces
import gymnasium as gym
import numpy as np

from game_controller import GameController
from action_manager import ActionManager
from state import State

class GameEnv(gym.Env):
    def __init__(self, action_manager: ActionManager, game_controller: GameController):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.game_controller = game_controller
        self.game_controller.wait_for_server()
        self.action_manager = action_manager
        self.stop_training = False
        self.action_space = spaces.Discrete(len(action_manager.actions))
        self.state = State({})
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.state.get_size(),), dtype=np.float32)
        self.player_memory = {
            "floor": 0,
            "act": 0,
        }

    def get_action_mask_from_commands(self, available_commands):
        mask = np.zeros(len(self.action_manager.actions), dtype=np.int8)
        available_set = set(available_commands)
        return_cmd_index = 125

        for i, action in enumerate(self.action_manager.actions):
            if action in available_set:
                mask[i] = 1

        mask[return_cmd_index] = 0 # Disable "Return" action

        return mask

    def get_action_mask(self):
        return self.get_action_mask_from_commands(self.state.available_commands)

    def reset(self, seed=None, options=None):
        raw = self.game_controller.get_state()
        self.state = State(raw)
        obs = self.state.encode_state()
        self.logger.info("Environment reset")
        return obs, {}

    def step(self, action):
        done = False
        actual_state = self.game_controller.get_state()
        self.state = State(actual_state)
        self.action_manager.update_actions(self.state.available_commands)
        action_name = self.action_manager.actions[action]

        self.game_controller.send_command(action_name)

        while True:
            new_state = self.game_controller.get_state()
            if self.game_controller.can_send_new_action(new_state["ready_for_command"], new_state["available_commands"]):
                break
            time.sleep(0.5)

        reward = self.compute_reward(new_state)

        if self.stop_training:
            done = True

        # update internal State and encode
        self.state = State(new_state)
        obs = self.state.encode_state()
        return obs, reward, done, False, {}

    def compute_reward(self, curr):
        reward = 0
        floor_reward = 0
        death_penalty = 0

        curr_gs = curr.get("game_state", {})
        curr_act = curr_gs.get("act", None)
        prev_floor = self.player_memory.get("floor")
        curr_floor = curr_gs.get("floor", None)
        floor_changed = (abs(curr_floor - prev_floor)) > 0
        floor_reward = curr_floor * 10 + (curr_act - 1) * 200
        if floor_changed:
            reward += floor_reward

        if curr_gs.get("screen_name", "") == "DEATH":
            death_penalty = floor_reward - 600
            self.stop_training = True
            reward += death_penalty

        self.player_memory["floor"] = curr_gs.get("floor", self.player_memory.get("floor"))

        self.logger.info(f"Reward obtained: {reward}")
        return reward
