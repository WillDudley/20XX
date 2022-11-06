import os.path
import melee

from melee_env.pettingzoo_env import MeleeEnv
from melee_env.agents.gymnasium_basic import CPUFox, RandomFox

players = [RandomFox(), CPUFox()]

env = MeleeEnv(players, os.path.expanduser('~/.melee/SSBM.ciso'), fast_forward=True)

max_episodes = 10

if __name__ == "__main__":
    env.start_emulator()

    for episode in range(max_episodes):
        observation, infos = env.reset(melee.enums.Stage.FOUNTAIN_OF_DREAMS)
        gamestate = infos["gamestate"]
        terminated = False
        while not terminated:
            actions = []
            for player in players:
                if player.agent_type == "CPU":  # CPU actions are handled internally
                    action = None
                else:
                    action = player.act(gamestate)
                actions.append(action)
            observation, reward, terminated, truncated, infos = env.step(actions=actions)
            gamestate = infos["gamestate"]
