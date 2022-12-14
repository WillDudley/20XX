import functools

from gymnasium import spaces

from melee_20XX.env.dconfig import DolphinConfig
import melee
from melee import enums
import numpy as np
import sys
import time
import pettingzoo as pz
from melee_20XX.env.spaces import observation_space, action_space, execute_action


class env(pz.ParallelEnv):
    metadata = {"render_modes": ["human"], "name": "Melee_v0"}

    def __init__(self,
        players,
        iso_path,
        fast_forward=False, 
        blocking_input=True,
        ai_starts_game=True):

        # ---- EMULATOR STUFF ----
        self.d = DolphinConfig()
        self.d.set_ff(fast_forward)

        self.iso_path = iso_path
        self.players = players

        # inform other players of other players
        # for player in self.players:
        #     player.set_player_keys(len(self.players))
        
        if len(self.players) == 2:
            self.d.set_center_p2_hud(True)
        else:
            self.d.set_center_p2_hud(False)

        self.blocking_input = blocking_input
        self.ai_starts_game = ai_starts_game

        self.gamestate = None

        # ---- OTHER STUFF ----
        self.possible_agents = ['Player_1', 'Player_2']


    def start_emulator(self):
        if sys.platform == "linux":
            dolphin_home_path = str(self.d.slippi_home)+"/"
        elif sys.platform == "win32":
            dolphin_home_path = None

        self.console = melee.Console(
            path=str(self.d.slippi_bin_path),
            dolphin_home_path=dolphin_home_path,
            blocking_input=self.blocking_input,
            tmp_home_directory=True)

        # print(self.console.dolphin_home_path)  # add to logging later
        # Configure Dolphin for the correct controller setup, add controllers
        human_detected = False

        for i in range(len(self.players)):
            curr_player = self.players[i]
            if curr_player.agent_type == "HMN":
                self.d.set_controller_type(i+1, enums.ControllerType.GCN_ADAPTER)
                curr_player.controller = melee.Controller(console=self.console, port=i+1, type=melee.ControllerType.GCN_ADAPTER)
                curr_player.port = i+1
                human_detected = True
            elif curr_player.agent_type in ["AI", "CPU"]:
                self.d.set_controller_type(i+1, enums.ControllerType.STANDARD)
                curr_player.controller = melee.Controller(console=self.console, port=i+1)
                self.menu_control_agent = i
                curr_player.port = i+1 
            else:  # no player
                self.d.set_controller_type(i+1, enums.ControllerType.UNPLUGGED)
            
        if self.ai_starts_game and not human_detected:
            self.ai_press_start = True

        else:
            self.ai_press_start = False  # don't let ai press start without the human player joining in. 

        if self.ai_starts_game and self.ai_press_start:
            self.players[self.menu_control_agent].press_start = True

        self.console.run(iso_path=self.iso_path)
        self.console.connect()

        [player.controller.connect() for player in self.players if player is not None]

        self.gamestate = self.console.step()


    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent: str) -> spaces.Space:
        return observation_space

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent: str) -> spaces.Space:
        return action_space

    def render(self) -> None:
        raise NotImplementedError("Rendering is implicitly handled by Dolphin - do not call this method. In the future we could disable rendering via https://github.com/altf4/libmelee/issues/87")
 
    def reset(self, stage):
        for player in self.players:
            player.defeated = False
            
        while True:
            self.gamestate = self.console.step()
            for i in range(2):
                melee.MenuHelper.menu_helper_simple(
                    gamestate=self.gamestate,
                    controller=self.players[i].controller,
                    character_selected=self.players[i].character,
                    stage_selected=stage,
                    connect_code="",
                    cpu_level=self.players[i].lvl,
                    costume=0,
                    autostart=True,
                    swag=False
                )

            if self.gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
                x_positions = [self.gamestate.players[i].position.x for i in list(self.gamestate.players.keys())]
                y_positions = [self.gamestate.players[i].position.y for i in list(self.gamestate.players.keys())]
                actions = [self.gamestate.players[i].action.value for i in list(self.gamestate.players.keys())]
                action_frames = [self.gamestate.players[i].action_frame for i in list(self.gamestate.players.keys())]
                hitstun_frames_left = [self.gamestate.players[i].hitstun_frames_left for i in
                                       list(self.gamestate.players.keys())]
                stocks = [self.gamestate.players[i].stock for i in list(self.gamestate.players.keys())]

                obs = np.array([x_positions, y_positions, actions, action_frames, hitstun_frames_left, stocks])

                info = {"gamestate": self.gamestate}

                return obs, info

    def close(self):
        for t, c in self.controllers.items():
            c.disconnect()
        self.observation_space._reset()
        self.gamestate = None
        self.console.stop()
        time.sleep(2)

    def step(self, actions=None):
        assert actions is not None, "Actions are handled in an OOP way."

        for i in range(2):
            if actions[i] is not None:
                execute_action(actions[i], self.players[i].controller)

        stocks = np.array([self.gamestate.players[i].stock for i in list(self.gamestate.players.keys())])
        done = not np.sum(stocks[np.argsort(stocks)][::-1][1:])

        if self.gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
            self.gamestate = self.console.step()

        x_positions = [self.gamestate.players[i].position.x for i in list(self.gamestate.players.keys())]
        y_positions = [self.gamestate.players[i].position.y for i in list(self.gamestate.players.keys())]
        actions = [self.gamestate.players[i].action.value for i in list(self.gamestate.players.keys())]
        action_frames = [self.gamestate.players[i].action_frame for i in list(self.gamestate.players.keys())]
        hitstun_frames_left = [self.gamestate.players[i].hitstun_frames_left for i in list(self.gamestate.players.keys())]
        stocks = [self.gamestate.players[i].stock for i in list(self.gamestate.players.keys())]

        obs = np.array([x_positions, y_positions, actions, action_frames, hitstun_frames_left, stocks])

        reward = 0

        terminated = done

        truncated = 0

        infos = {"gamestate": self.gamestate}

        return obs, reward, terminated, truncated, infos
