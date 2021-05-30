class Goal:
    def __init__(self, name, count):
        self.name = name
        self.count = count


class Status:
    def __init__(self, minerals, vespin, unaries, workers, ves_rat, min_rat):
        self.minerals = minerals
        self.vespin = vespin
        self.unaries = unaries
        self.idle_workers = workers
        self.VR = ves_rat
        self.MR = min_rat

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        out = "Status"
        out += "\nMinerals:" + str(self.minerals)
        out += "\nVespin:" + str(self.vespin)
        out += "\nUnaries:" + str(self.unaries)
        out += "\n-------------------------------------"
        return out

    def check(self, goal):
        if goal.name in self.unaries:
            # print(str(goal.count)+"Pylons"+str(self.unaries[goal.name]))
            return goal.count <= self.unaries[goal.name]
        else:
            return False

    def unplan_action(self, action):
        print("Unplanning: " + str(action))
        self.minerals += action.minerals
        self.vespin += action.vespin
        self.idle_workers += action.workers
        for c in action.unary_cost:
            self.unaries[c] += action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]

    def undo_action(self, action):  # znovu rozplánuje akci
        print("Undoing: " + str(action))
        self.idle_workers -= action.workers
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]
        for e in action.effect:
            if not (e in self.unaries):
                self.unaries[e] = 0
            self.unaries[e] -= action.effect[e]

    def start_action(self, action):
        self.minerals -= action.minerals
        self.vespin -= action.vespin
        self.idle_workers -= action.workers
        print("Startting: " + str(action))
        for c in action.unary_cost:
            self.unaries[c] -= action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]

    def end_action(self, action):
        self.idle_workers += action.workers
        print("Finishing: " + str(action))
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]
        for e in action.effect:
            if not (e in self.unaries):
                self.unaries[e] = 0
            self.unaries[e] += action.effect[e]

    def is_plannable(self, action):
        for c in action.unary_cost:
            if c not in self.unaries[c]: return False
        for b in action.burrow:
            if b not in self.unaries[b]: return False
        for r in action.prereq:
            if r not in self.unaries[r]: return False

        return True

    def waited(self, passed_time):
        # TODO: Worker Manager
        self.minerals += self.MR * passed_time
        self.vespin += self.VR * passed_time

    def relapsed(self, passed_time):
        self.minerals -= self.MR * passed_time
        self.vespin -= self.VR * passed_time

    def project(self, minerals, vespin):
        if minerals <= self.minerals:
            mineral_time = 0
        else:
            mineral_time = round((minerals - self.minerals) / self.MR)

        if vespin <= self.vespin:
            vespin_time = 0
        else:
            vespin_time = round((vespin - self.vespin) / self.VR)

        if vespin_time < mineral_time:
            return mineral_time
        else:
            return vespin_time