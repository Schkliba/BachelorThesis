# Naive implementation
# workers are permanent
# workers don't need to move
# units are bound by population limit

# thrifty algorithm: if there are resources, they are going to be spent
# two timers - vespin and minerals

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

    def check(self, goal):
        if goal.name in self.unaries:
            return goal.count >= self.unaries[goal.name]
        else:
            return False

    def unplan_action(self, action):
        self.minerals += action.min
        self.vespin -= action.vespin
        self.idle_workers += action.workers
        for c in action.unary_cost:
            self.unaries[c] += action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]

    def undo_action(self, action):
        self.idle_workers -= action.workers
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]
        for e in action.effect:
            if not (e in self.unaries):
                self.unaries[e] = 0
            self.unaries[b] -= action.effect[e]

    def start_action(self, action):
        self.minerals -= action.min
        self.vespin -= action.vespin
        self.idle_workers -= action.workers

        for c in action.unary_cost:
            self.unaries[c] -= action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]

    def end_action(self, action):
        self.idle_workers += action.workers
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]
        for e in action.effect:
            if not (e in self.unaries):
                self.unaries[e] = 0
            self.unaries[b] += action.effect[e]

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

    def project(self, minerals, vespin):
        if minerals <= self.minerals:
            mineral_time = 0
        else:
            mineral_time = (minerals - self.minerals) / self.MR

        if vespin <= self.vespin:
            vespin_time = 0
        else:
            vespin_time = (vespin - self.vespin) / self.VR

        if vespin_time < mineral_time:
            return mineral_time
        else:
            return vespin_time


class ActionPool:
    def __init__(self):
        self.connected = False
        self.referencee_state = None
        self.actions = []
        self.plannable = []
        self.idle_action = None
        self.unplannable = []

    def register_action(self, action):
        self.actions += [action]

    def connect(self, state):
        self.referencee_state = state
        for a in self.actions:
            if state.isplannable(a):
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

    def schedule(self, from_t):
        return ScheduledAction(self.min, self.vespin, self.prereq, self.unary_cost,
                               self.burrow, self.duration, self.effect, from_t)


class ScheduledAction(Action):
    def __init__(self, minerals, gas, prereq, cost, burrow, duration, effect, start_time):
        super().__init__(minerals, gas, prereq, cost, burrow, duration, effect)
        self.start_time = start_time
        self.end_time = start_time + duration
        self.surplus_time = 0

    def add_time(self, time):
        self.surplus_time = time
        self.duration += time
        self.end_time += time


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
        self.actions = sorted(self.end_actions, key=self.key)

    def delete(self, action):
        self.actions.remove(action)

    def __getitem__(self, item):
        return self.actions[item]

    def __len__(self):
        return len(self.actions)


class PlanningWindow:  # ukládání plánu v časové souvislosti
    def __init__(self, timeline=Timeline("ef")):
        self.time = 0
        self.last_done = -1
        self.finish_time = 0
        self.time_line = timeline  # invariant: akce s menším indexem končí dřív
        self.a_order = []  # ukládá akce v pořadí v němž byly naplánovány. tj. řazení dle času začátku

    def plan_action(self, sch_a):
        self.time_line.add_action(sch_a)
        self.a_order.append(sch_a)

    def unplan_last(self):
        action = self.a_order[len(self.a_order) - 1]
        self.time_line.delete(action)
        self.time = action.start_time
        return action

    def first2finish(self):  # vrací
        assert self.last_done + 1 < len(self.time_line)
        return self.time_line[self.last_done + 1].end_time

    def rewind_to(self, time):
        opened_actions = []
        for i in range(self.last_done, 0, -1):
            if self.time_line[i].end_time >= time:
                opened_actions += [self.time_line[i]]
                self.last_done = i
        return opened_actions

    def finish_everything_prior(self, time):
        finish_list = []
        if time < self.time: raise RuntimeError("Action Finishing: Cannot go back in time!")

        for i in range(self.last_done + 1, len(self.time_line)):
            if self.time_line[i].end_time <= time:
                finish_list += [self.time_line[i]]
                self.last_done = i

        self.time = time
        return finish_list


class Game:
    def __init__(self, init_state, actions):
        self.window = PlanningWindow()
        self.state = init_state
        self.CT = 0
        self.MT = 0
        self.VT = 0
        self.action_pool = actions
        self.action_pool.connect(self.state)

    def current_time(self):
        return self.CT

    def unplan_last(self):
        action = self.window.unplan_last()
        self.state.unplan_action(action)

    def update(self, goals):
        for g in goals:
            if self.state.check(g):
                goals.remove(g)
        return goals.empty()

    def planable_actions(self):
        assert self.action_pool.plannable is not None
        return self.action_pool.plannable

    def update_time(self, new_time):
        assert new_time > self.CT
        if self.MT < new_time: self.MT = new_time
        if self.VT < new_time: self.VT = new_time
        self.state.waited(new_time - self.CT)
        self.CT = new_time
        return self.window.finish_everything_prior(new_time)

    def finish_actions(self, actions):

        for a in actions:
            self.state.end_action(a)

    def plan_next_action(self, action):
        action = action.schedule(self.CT)
        surplus_time = self.state.project(action.minerals, action.vespin)
        action.add_time(surplus_time)
        self.window.plan_action(action)
        self.state.start_action(action)

    def first_finished_time(self):
        return self.window.first2finish()

    def reverse(self, time):  # finished action
        actions = self.window.rewind_to(time)
        for a in actions:
            self.state.undo_action(a)


def betterplan(planA, planB):
    return planA.time <= planB.time


def AstarSearch(game, actions, schedule, goals, ub_time):
    # actions = goals.relevant_actions()
    # schedule = game.schedule
    state = game.state
    for g in goals:
        if state.check(g):
            goals.remove(g)
    for a in actions:
        schedule.plan_action(a)
        bestplan = AStarDFS(game, goals, 0, [], ub_time)
        schedule.unplan_last()

    return bestplan


def AStarDFS(game, goals, current_time, bestplan, ub_time):
    if current_time >= ub_time:
        print("Limitní čas...")
        return game.get_plan()

    isdone = game.update(goals)
    if isdone:
        print("Vyhráli jsme!")
        return game.get_plan()

    plan_act = game.plannable_actions()

    # planovatelné akce od tohoto okamžiku
    for a in plan_act:
        new_current_time = game.shift_plan_action(a)
        plan = AStarDFS(game, goals, new_current_time, ub_time)
        if betterplan(plan, bestplan):
            bestplan = plan

        game.unplan_last()

    bookmark = game.current_time()
    new_current_time = game.first_finished_time()
    finished_actions = game.update_time(new_current_time)
    game.finish_actions(finished_actions)

    # plánování akcí po dokončení první dokončitelné_akce
    plan = AStarDFS(game, goals, new_current_time, ub_time)
    if betterplan(plan, bestplan):
        bestplan = plan

    game.reverse(bookmark)
    return bestplan

for i in range(0,0,-1):
    print(i)

