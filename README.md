20XX
---
`from melee_20XX import Melee_v0`

20XX is a PettingZoo-based library for Melee. (⌐■_■)

## Code Example
```python
import os.path
import melee

from melee_20XX import Melee_v0
from melee_20XX.agents.basic import CPUFox, RandomFox

players = [RandomFox(), CPUFox()]

env = Melee_v0.env(players, os.path.expanduser('~/.melee/SSBM.ciso'), fast_forward=True)

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
```

## Note
This library requires Slippi, which in turn requires an SSBM 1.02 NTSC/PAL ISO. This library does not and will not distribute this. You must acquire this on your own!

## Installation
1. `pip install 20XX`
2. `pip install git+https://github.com/WillDudley/libmelee.git`  (fixes some menu handling issues)

## Credits
- Heavily relies on [libmelee](https://github.com/altf4/libmelee),
- uses [PettingZoo](https://pettingzoo.farama.org),
- originally forked from [melee-env](https://github.com/davidtjones/melee-env).
