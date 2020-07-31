import copy
class Plan:
    def __init__(self, timeline):
        self.plan = []
        for a in timeline:
            self.plan += [copy.deepcopy(a)]

        if len(self.plan) > 0:
            self.time = timeline[len(timeline) - 1].end_time
        else:
            self.time = 0

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        out = "["
        for a in self.plan:
            out += str(a) + ","
        out += "]"
        return out


class MockPlan:
    def __init__(self, time):
        self.time = time

    def __str__(self):
        return "Mock Plan"

class Timeline:  # objekt pro držení pořadí akcí podle času ukončení

    def __init__(self, type):
        self.actions = []  # TODO iplementace jako strom
        self.key = Timeline.get_end
        if type == "sf":
            self.key = Timeline.get_start

    @staticmethod
    def get_end(elem):
        return elem.end_time

    @staticmethod
    def get_start(elem):
        return elem.start.time

    def add_action(self, action):
        self.actions += [action]
        self.actions = sorted(self.actions, key=self.key)

    def delete(self, action):
        self.actions.remove(action)
        self.actions = sorted(self.actions, key=self.key)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        out = "["
        for a in self.actions:
            out += str(a) + ","
        out += "]"
        return out

    def __getitem__(self, item):
        if item >= len(self.actions): raise IndexError("Out of bounds")
        return self.actions[item]

    def __len__(self):
        return len(self.actions)