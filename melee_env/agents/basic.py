from melee import enums
from melee_env.agents.spaces_util import observation_space, action_space, execute_action

class CPUFox:
    def __init__(self, press_start=False):
        self.agent_type = "CPU"
        self.controller = None
        self.port = None  # this is also in controller, maybe redundant?
        self.action = 0
        self.press_start = press_start
        self.self_observation = None
        self.current_frame = 0
        self.character = enums.Character.FOX
        self.lvl = 9

    def act(self, gamestate):
        pass


class RandomFox:
    def __init__(self, press_start=False):
        self.agent_type = "AI"
        self.controller = None
        self.port = None  # this is also in controller, maybe redundant?
        self.action = 0
        self.press_start = press_start
        self.self_observation = None
        self.current_frame = 0
        self.character = enums.Character.FOX
        self.action_space = action_space
        self.lvl = 0

    def act(self, gamestate):
        action = self.action_space.sample()
        # execute_action(action, self.controller)
        return action