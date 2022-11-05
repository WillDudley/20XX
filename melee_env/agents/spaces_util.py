import numpy as np
from gymnasium.spaces import Box, MultiDiscrete

# TODO: libmelee gamestate to gymnasium observation space, gymnasium action space to libmelee action space

x_bounds = (-1000, 1000)  # guess
y_bounds = (-1000, 1000)  # guess
action_bounds = (0, 3)  # guess
action_frame_bounds = (0, 1000)  # guess
remaining_hitstun_frames_bounds = (0, 1000)  # guess
stocks_bounds = (0, 4)  # guess

observation_space = Box(low=np.array([x_bounds[0], y_bounds[0], action_bounds[0], action_frame_bounds[0], remaining_hitstun_frames_bounds[0], stocks_bounds[0]]),
                        high=np.array([x_bounds[1], y_bounds[1], action_bounds[1], action_frame_bounds[1], remaining_hitstun_frames_bounds[1], stocks_bounds[1]]),
                        dtype=np.float32)

# 9 cardinal directions:
# np.array([[0.0, 0.0],  # no op
#           [0.0, 1.0],
#           [mid, mid],
#           [1.0, 0.0],
#           [mid, -mid],
#           [0.0, -1.],
#           [-mid, -mid],
#           [-1., 0.0],
#           [-mid, mid]])
# 5 buttons:
# NO-OP
# A
# B
# Z
# R
action_space = MultiDiscrete([9, 5])
