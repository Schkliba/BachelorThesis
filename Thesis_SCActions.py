import copy

class ActionPool:

    def __init__(self):
        self.connected = False
        self.ref_state = None
        self.actions = []
        self.plannable = []
        self.idle_action = None
        self.unplannable = []

    def __repr__(self):
        out = "["
        for a in self:
            out += str(a)
        out += "]"
        return out

    def __str__(self):
        return self.__repr__()

    def __iter__(self):
        return self.plannable.__iter__()

    def register_action(self, action):
        self.actions += [action]

    def connect(self, state):
        self.ref_state = state
        for a in self.actions:
            if state.is_plannable(a):
                self.plannable += [a]

    def refresh(self):
        self.plannable = []
        for a in self.actions:
            if self.ref_state.is_plannable(a):
                self.plannable += [a]





class Action:
    def __init__(self, name, workers, minerals, gas, prereq, cost, burrow, duration, effect):
        self.name = name
        self.minerals = minerals
        self.vespin = gas
        self.prereq = prereq  # před
        self.unary_cost = cost  # zničené suroviny
        self.workers = workers
        self.burrow = burrow  # propujčené suroviny
        self.duration = duration
        self.effect = effect  # po

    def __str__(self):
        return self.name

    def schedule(self, from_t):
        return ScheduledAction(self.name, self.workers, self.minerals, self.vespin, self.prereq, self.unary_cost,
                               self.burrow, self.duration, self.effect, from_t)


class ScheduledAction(Action):
    def __init__(self, name, workers, minerals, gas, prereq, cost, burrow, duration, effect, start_time):
        super().__init__(name, workers, minerals, gas, prereq, cost, burrow, duration, effect)
        self.start_time = start_time
        self.end_time = start_time + duration
        self.surplus_time = 0
        self.finished = False

    def add_time(self, time):
        self.surplus_time = time
        self.duration += time
        self.end_time += time

    def __eq__(self, other):
        return (self.name == other.name) and (self.start_time == other.start_time) and (
        self.duration == other.duration) and (self.finished == other.finished)

    def __str__(self):
        return str(self.name) + " (" + str(self.end_time) + str(self.finished) + ")"