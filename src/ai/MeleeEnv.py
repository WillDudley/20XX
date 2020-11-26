from src.config.project import Project
import numpy as np
import melee
import code

    
class MeleeEnv:
    """
    model gym
    """
    def __init__(self, fast_forward=False):
        self.project = Project()
        self.project.set_ff(fast_forward)

        # TODO: pass as argument w/ base class so it's easy to compare
        #       different action and observation spaces.
        self.action_space = ActionSpace()  
        self.observation_space = ObservationSpace()
        self.gamestate = None

        self.console = melee.Console(
            path=str(self.project.slippi_bin),
            #  blocking_input=True)  # broken atm
        )
        
        self.controllers = {
            'ai': melee.Controller(console=self.console, port=1),
            'cpu': melee.Controller(console=self.console, port=2)
            
        }

        self.console.run(iso_path=self.project.iso)
        self.console.connect()

        for type, controller in self.controllers.items():
            controller.connect()

    def setup(self):
        while True:
            self.gamestate = self.console.step()
            if self.gamestate.menu_state is melee.Menu.CHARACTER_SELECT:
                melee.MenuHelper.choose_character(character=melee.enums.Character.FOX,
                                                  gamestate=self.gamestate,
                                                  controller=self.controllers['ai'],
                                                  costume=2,
                                                  swag=False,
                                                  start=False)

                melee.MenuHelper.choose_character(character=melee.enums.Character.FOX,
                                                  gamestate=self.gamestate,
                                                  controller=self.controllers['cpu'],
                                                  cpu_level=1,
                                                  swag=False,
                                                  start=True)

            elif self.gamestate.menu_state is melee.Menu.STAGE_SELECT:
                melee.MenuHelper.choose_stage(stage=melee.enums.Stage.FINAL_DESTINATION,
                                              gamestate=self.gamestate,
                                              controller=self.controllers['ai'])

            elif self.gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
                return None, None, False, None

            else:
                melee.MenuHelper.choose_versus_mode(self.gamestate, self.controllers['ai'])


    def step(self, action=0):
        if self.gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
            # execute controller input for selected action:
            controller_input = self.action_space(action)
            controller_input.execute(self.controllers['ai'])    

            # step env
            self.gamestate = self.console.step()

            # get updated observation
            return self.observation_space(self.gamestate)
        else:
            for t, c in self.controllers.items():
                c.release_all()
            return None, None, True, None


class ObservationSpace:
    def __init__(self):
        self.size = None
        self.previous_gamestate = None
        self.current_gamestate = None

    def get_percents(self):
        # return a array [(damage done, damage taken)]
        current = np.array([
            self.current_gamestate.player[1].percent,
            self.current_gamestate.player[2].percent])
        if self.previous_gamestate is not None:
            previous = np.array([
                self.previous_gamestate.player[1].percent,
                self.previous_gamestate.player[2].percent])
        
            diff = current - previous
        else:
            diff = np.array([0, 0])

        return np.array([diff, current])

    def get_stocks(self):
        # return a tuple (p1 stocks lost, p2 stocks lost)
        current = np.array([
            self.current_gamestate.player[1].stock, 
            self.current_gamestate.player[2].stock])

        if self.previous_gamestate is not None:
            previous = np.array([
                self.previous_gamestate.player[1].stock, 
                self.previous_gamestate.player[2].stock])

            diff = current - previous
        else:
            diff = np.array([0, 0])
        return np.array([diff, current])

    def get_positions(self):
        facing = (self.current_gamestate.player[1].facing, 
                  self.current_gamestate.player[2].facing)

        x = (self.current_gamestate.player[1].x, 
             self.current_gamestate.player[2].x)

        y = (self.current_gamestate.player[1].y, 
             self.current_gamestate.player[2].y)

        return np.array([facing, x, y])

    def get_actions(self):
        action = (self.current_gamestate.player[1].action.value, 
                  self.current_gamestate.player[2].action.value)

        action_frame = (self.current_gamestate.player[1].action_frame, 
                        self.current_gamestate.player[2].action_frame)
        
        return np.array([action, action_frame])
        

    def __call__(self, gamestate):
        """ pull out relevant info from gamestate """
        self.current_gamestate = gamestate
        total_reward = 0
        
        stocks = self.get_stocks()
        percents = self.get_percents()
        
        # reward/penalize based on delta damage/stocks
        total_reward -= 100 * stocks[0][0]
        total_reward += 100 * stocks[0][1]

        total_reward -= stocks[0][0]
        total_reward += stocks[0][1]

        position = self.get_positions()
        actions = self.get_actions()

        self.previous_gamestate = self.current_gamestate
        done = not (bool(stocks[1][0]) or bool(stocks[1][1]))
        
        return (stocks, percents, position, actions), total_reward, done, None

class ActionSpace:
    def __init__(self):
        self.button_space = np.array([0.0, 1.0])
        self.shoulder_space = np.array([0.0,          # none
                                        # 0.1,         # light press
                                        1.0])         # hard press    
        
        self.c_stick_space = np.array([[0.0, 0.0],    # center
                                       [1.0, 0.0],    # right
                                       [0.0, -1.0],   # down
                                       [-1.0, 0.0],   # left
                                       [0.0, 1.0]])   # up
        
        # The main control stick is slightly harder as there isn't a simple
        #   square stick box, so some calculation is needed to find legal 
        #   values. Also of note, the space of values of the stick needs to
        #   include no-op, so an odd value must be used on the number of 
        #   steps. 
        self.stick_values = np.linspace(-1, 1, (2**3)-1)
        
        # create tuples of all possible stick values:
        self.stick_space_square = np.array(
            np.meshgrid(self.stick_values, self.stick_values)).T.reshape(-1, 2)

        # These contain illegal values in a circular stick box, you can never
        #   achieve (1,1), for example. For any values a and b,  a^2 + b^2 > 1 
        #   are thus illegal. 
        dist = np.sqrt(
            self.stick_space_square[:, 0]**2 + self.stick_space_square[:, 1]**2)
        legal_indices = np.where(dist <= 1)

        self.stick_space_circle = self.stick_space_square[legal_indices]

        mid = np.sqrt(2)/2

        self.stick_space_reduced = np.array([[0.0, 0.0], # no op
                                             [0.0, 1.0],
                                             [mid, mid],
                                             [1.0, 0.0],
                                             [mid, -mid],
                                             [0.0, -1.],
                                             [-mid, -mid],
                                             [-1., 0.0],
                                             [-mid, mid]])

        self.button_space_reduced = np.array([0., 1., 2., 3., 4.])

        # Action space size is total number of possible actions. In this case,
        #    is is all possible main stick positions * all c-stick positions *
        #    all the buttons. A normal controller has ~51040 possible main stick 
        #    positions. Each trigger has 255 positions. The c-stick can be 
        #    reduced to ~5 positions. Finally, if all buttons can be pressed
        #    in any combination, that results in 32 combinations. Not including
        #    the dpad or start button, that is 51040 * 5 * 255 * 2 * 32 which 
        #    is a staggering 4.165 billion possible control states. 

        # Given this, it is reasonable to reduce this. In the above class, the 
        #    main stick has been reduced to the 8 cardinal positions plus the 
        #    center (no-op). Only A, B, Z, and R are used, as these correspond
        #    to major in-game functions (attack, special, grab, shield). Every
        #    action can theoretically be performed with just these buttons. A 
        #    final "button" is added for no-op. 
        #
        #    Action space = 9 * 5 = 45 possible actions. 
        self.action_space = np.zeros((self.stick_space_reduced.shape[0] * self.button_space_reduced.shape[0], 3))

        for button in self.button_space_reduced:
            self.action_space[int(button)*9:(int(button)+1)*9, :2] = self.stick_space_reduced
            self.action_space[int(button)*9:(int(button)+1)*9, 2] = button

        self.size = self.action_space.shape[0]

    def sample(self):
        return np.random.choice(self.size)

    def __call__(self, action):
        if action > self.size - 1:
            exit("Error: invalid action!")

        return ControlState(self.action_space[action])


class ControlState:
    def __init__(self, state):
        self.state = state
        self.buttons = [
            melee.enums.Button.BUTTON_A,
            melee.enums.Button.BUTTON_B,
            melee.enums.Button.BUTTON_R,
            melee.enums.Button.BUTTON_Z]

    def execute(self, controller):
        controller.release_all()      # reset everything real quick
        if self.state[2] != 0.0:      # no-op
            if self.state[2] != 4.0:  # R shoulder
                controller.press_button(self.buttons[int(self.state[2])-1]) 
            else:
                controller.press_shoulder(melee.enums.Button.BUTTON_R, 1)
        
        controller.tilt_analog_unit(melee.enums.Button.BUTTON_MAIN, 
                                    self.state[0], self.state[1])



if __name__ == "__main__":
    import code
    asp = ActionSpace()
    code.interact(local=locals())