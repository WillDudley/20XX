import numpy as np
from gymnasium.spaces import Box, MultiDiscrete
import melee

# TODO: libmelee gamestate to gymnasium observation space, gymnasium action space to libmelee action space

x_bounds = (-1000, 1000)  # guess
y_bounds = (-1000, 1000)  # guess
action_bounds = (0, 3)  # guess
action_frame_bounds = (0, 1000)  # guess
remaining_hitstun_frames_bounds = (0, 1000)  # guess
stocks_bounds = (0, 4)  # guess

observation_space = Box(low=np.array(
    [x_bounds[0], y_bounds[0], action_bounds[0], action_frame_bounds[0], remaining_hitstun_frames_bounds[0],
     stocks_bounds[0]]),
                        high=np.array([x_bounds[1], y_bounds[1], action_bounds[1], action_frame_bounds[1],
                                       remaining_hitstun_frames_bounds[1], stocks_bounds[1]]),
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


def execute_action(action, controller):
    control_stick_action = action[0]
    button_action = action[1]

    control_stick_mapping = [
        [0., 0.],
        [0., 1.],
        [0.70710678, 0.70710678],
        [1., 0.],
        [0.70710678, -0.70710678],
        [0., -1.],
        [-0.70710678, -0.70710678],
        [-1., 0.],
        [-0.70710678, 0.70710678]]
    button_mapping = [
        False,
        melee.enums.Button.BUTTON_A,
        melee.enums.Button.BUTTON_B,
        melee.enums.Button.BUTTON_Z,
        melee.enums.Button.BUTTON_R
    ]

    controller.release_all()
    if button_action != 0:
        if button_action == 4:
            controller.press_shoulder(melee.enums.Button.BUTTON_R, 1)
        else:
            controller.press_button(button_mapping[button_action])
    controller.tilt_analog_unit(melee.enums.Button.BUTTON_MAIN,
                                control_stick_mapping[control_stick_action][0],
                                control_stick_mapping[control_stick_action][1])

    return
