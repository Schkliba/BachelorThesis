#Úkolem je najít 
#nebreme ohled na samotné dělníky
#
TIME_STEP = 240 # 10s * 24frame
import heapq
class Goal:
    def __init__(self,product,number,progress_bar):
        self.prod = product
        self.count = number
        self.stage = progress_bar
class Map:
    def __init__(self, mine, gas, init_product):
        self.grounded_actions = []
        self.placeholder_actions = []
        self.mining_actions = []

        self.gas = gas
        self.mine = mine
        self.popcap = 0

        self.ph_gas = 0
        self.ph_mine = 0

        self.g_deposit_workers = 0
        self.m_deposit_workers = 0

        self.idle = dict()
        self.in_action = dict()
        self.placeholding = dict()
        self.produced = init_product

    def possible_actions(self,mine,gas):
        possible_actions = []
        for i in range(len(self.grounded_actions)):
            if self.has_resources_for(self.grounded_actions[i]):
                possible_actions += [self.grounded_actions[i]]
            else:
                possible_actions += [self.placeholder_actions[i]]

        return possible_actions + self.mining_actions

    def begin(self,action):
        if action.type == "grounded":
            self.gas -= action.gas
            self.mine -= action.mine
            self.idle[action.labour] -= 1
            self.in_action[action] += 1
        elif action.type == "placeholder":
            self.ph_gas += action.gas
            self.ph_mine += action.mine
            self.idle[action.labour] -= 1
            self.placeholding[action] += 1

    def wrap_up(self, action):
        if action.type == "grounded":
            for product in action.produced:
                self.produced[product] += action.produced[product]
            self.in_action[action.labour] -= 1
            self.idle[action.labour] += 1
        elif action.type == "placeholder":
            self.ph_gas -= action.gas
            self.ph_mine -= action.mine
            self.idle[action.labour] -= 1
            self.placeholding[action] += 1

class MonoMap(Map):
    def __init__(self,location,avg_time):
        self.location = location
        self.time = avg_time

    def ground_actions(self):
        pass


class Plan:
    def __init__(self):
        self.pq = []
    def add(self,action, time):
        end = action.duration + time
        heapq.heappush(self.pq, (end,action))

    def pop(self):
        return heapq.heappop(self.pq)

class Action:
    #to/from
    def __init__(self, name, miner, gas, labour = "worker", consume = dict(), produce = dict(), duration = 0):
        self.name = name
        self.gas = gas
        self.miner = miner
        self.labour = labour
        self.consume = consume
        self.produce = produce
        self.duration = duration

class GroundedAction:
    #predicate name:(location,number)


class State:
    def __init__(self, gas, mine, actions, map):

        self.timeline = 0
        self.actions = actions
        self.map = map

    def ground_actions(self):
        pass

    def reached(self,goals):
        pass

    def framed_possible_actions(self,timeframe):
        mine_rate = map.mine_rate()
        gas_rate = map.gas_rate()
        mine_up = mine_rate * timeframe + self.mine
        gas_up = gas_rate * timeframe + self.gas
        actions = map.possible_action(self,mine_up, gas_up)
        return actions

def IDAS(game_state, plan, upper_bound):

    for depth_limit in range(0, upper_bound):
        t = DLS(game_state, plan, bound, depth_limit)
        if t > bound: return None
        else: bound = t
    return False

def DLS(game_state, plan, bound):
    # If reached the maximum depth,
    # stop recursing.

    t = plan.first_idle_worker()
    f = t + game_state.h()
    if f > bound: return f
    if game_state.are_goals_reached():
        return f
    actions = game_state.framed_possible_actions()
    minimum = bound
    for action in actions:
        plan.add(action,f)
        game_state.apply(action)
        result_time = DLS(game_state, plan, bound)
        if result_time < minimum: minimum = result_time
        game_state.revert(action)
        plan.pop(action,f)

    return minimum