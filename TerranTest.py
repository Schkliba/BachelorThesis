#Naive implementation
# workers don't need to move
# units are bound by population limit

# thrifty algorithm: if there are resources, they are going to be spent
# two timers - vespin and minerals
import copy
import math
from typing import List
from actions import *
from ActionState import Status
import time


class Goal:
    def __init__(self, name,count,weight = 1):
        self.name = name
        self.weight = weight
        self.count = count

class Plan:
    def __init__(self,timeline):
        self.plan = []
        for id,a in timeline:
            z = copy.deepcopy(a)
            z.finished = True
            self.plan += [z]

        if len(self.plan) > 0:
            self.time = timeline.end_time
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
    def __len__(self):
        return len(self.plan)
    def __iter__(self):
        return self.plan.__iter__()


class MockPlan:
    def __init__(self, time: int, distance: int):
        self.distance = distance
        self.time = time

    def __str__(self):
        return "Mock Plan ("+str(self.time)+","+str(self.distance)+")"


class Timeline: #objekt pro držení pořadí akcí podle času ukončení

    def __init__(self, type):
        self.actions = [] #TODO iplementace jako strom
        self.key = Timeline.get_end
        if type == "sf":
            self.key = Timeline.get_start
        self.end_time = 0

    @staticmethod
    def get_end(elem):
        return elem.end_time

    @staticmethod
    def get_start(elem):
        return elem.start.time


    def add_action(self, id, action):
        self.actions += [(id,action)]
        self.actions = sorted(self.actions, key=lambda x: self.key(x[1]))
        n_id, end_a = self.actions[len(self.actions)-1]
        self.end_time = end_a.end_time

    def delete(self,id, action):
        self.actions.remove((id,action))
        self.actions = sorted(self.actions, key= lambda x: self.key(x[1]))
        if len(self.actions) > 0:
            n_id, end_a = self.actions[len(self.actions) - 1]
            self.end_time = end_a.end_time
        else:
            self.end_time = 0

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


class TimePoint:
    def __init__(self):
        self.current_point = 0


class PlanningWindow: #ukládání plánu v časové souvislosti

    def __init__(self, timeline=Timeline("ef")):
        self.time = 0
        self.last_done = -1
        self.finish_time = 0
        self.time_line = timeline #invariant: akce s menším indexem končí dřív
        self.a_order = [] #ukládá akce v pořadí v němž byly naplánovány. tj. řazení dle času začátku

    def _plan_action(self, act: ScheduledAction):
        self.time_line.add_action(self.gen_action_ID(),act)
        self.a_order = [act]+self.a_order

    def plan_action(self, act: ScheduledAction):
        self._plan_action(act)
        return act

    def plan_finished_action(self, act: ScheduledAction): #TODO: Je potřeba zavolat finish
        self._plan_action(act)
        return act

    def gen_action_ID(self):
        return len(self.a_order)

    def get_potential(self):
        return self.time_line.end_time


    def get_plan(self):
        return Plan(self.time_line)

    def unplan_action(self, action: ScheduledAction):
        self.time_line.delete(self.gen_action_ID()-1,action)
        self.a_order.remove(action)

    def last(self):
        if len(self.a_order)<1: return None
        action = self.a_order[0]
        return action

    def __str__(self):
        return str(self.time_line)

    def rewind_to(self, time):
        opened_actions = []
        self.time = time
        for i in range(len(self.time_line)-1, -1, -1):
            id, action = self.time_line[i]
            if action.end_time <= time:
                self.last_done = i
                break
            z = self.time_line[i]
            opened_actions += [z]
        return opened_actions

    def finish_everything_prior(self,time):
        finish_list = []
        if time < self.time: raise RuntimeError("Action Finishing: Cannot go back in time!")

        for i in range(len(self.time_line)):
            id, a = self.time_line[i]
            if a.end_time <= time and not a.finished:
                finish_list += [a]
                a.finished = True
                self.last_done = i

        self.time = time
        return finish_list

class Game:

    def __init__(self, init_state: Status, actions: ActionPool, duration_graph, resource_graph, max_bounds = {}):
        self.window = PlanningWindow()
        self.w_calendar = {}
        self.state = init_state
        self.action_pool = actions
        self.action_pool.connect(self.state)
        self.max_depth = 0
        self.max_bounds = max_bounds
        self.h_duration = duration_graph
        self.h_resources = resource_graph
        self.node_count = 0
        self.finished_branches = 0
        self.good_branches = 0
        self.id_check = 0
        self.hot_time = 0
    def CT(self):
        return self.window.time

    def is_over_bounds(self):
        for u in self.max_bounds:
            if u not in self.state.unaries:
                continue
            if self.state.unaries[u].shadow > self.max_bounds[u]:
                return True
        return False

    def unplan_last(self):
        action = self.window.unplan_last()
        self.state.unplan_action(action)

    def goal_metrics(self, goals):
        plan_distance = 0
        minerals = 0
        vespin = 0

        for g in goals:
            progress = self.state.check(g)
            # isdone?
            plan_distance += progress
            minerals += self.action_pool.by_name[g.name].minerals * progress
            vespin += self.action_pool.by_name[g.name].vespin * progress
        return plan_distance

    def check_id(self,action):
        if self.id_check <= action.id:
            return True
        else:
            return False

    def update(self,goals):
        return self.goal_metrics(goals)


    def refresh(self, at_time):
        assert at_time >= self.CT()
        self.state.get_to(at_time)
        return self.window.finish_everything_prior(at_time)

    def finish_actions(self,actions):
        for a in actions:
            a.finish = True
            #self.state.end_action(a)

    def time_shift(self, new_time):
        self.window.time = new_time

    def plan_next_action(self, action: Action):
        sch_a = self.__plan_acton(action)
        self.window.plan_action(sch_a)
        return sch_a.start_time #TODO:

    def __plan_acton(self,action):

        surplus_time = self.state.when(action) - self.state.CT
        print("Surplus!"+str(surplus_time))
        assert surplus_time < math.inf
        z = time.time()
        sch_a = action.schedule(self.CT())

        sch_a.add_time(surplus_time)

        self.state.plan_action(sch_a)
        w = time.time()

        return sch_a

    def check_triggers(self,action)->List[Action]:
        response = []
        for t in self.triggers:
            act = self.triggers[t].validate(action)
            if not (act is None): response += [act]
        return response


    def reverse(self,time): #finished action
        last = self.window.last()
        self.state.unplan_action(last)
        self.window.unplan_action(last)
        self.state.return_to(time)
        self.window.rewind_to(time)


    def get_plan(self, distance):
        return self.window.get_plan()

    def potential_end(self, goals):
        new_state = {}
        new_goals = {}
        simple_state = set()

        for g in goals:
            new_goals[g.name] = g.count
        for u in self.state.unaries:
            if self.state.unaries[u].shadow > 0:
                new_state[u] = self.state.unaries[u].shadow
                if u not in new_goals or new_state[u] >= new_goals[u]:
                    simple_state.add(u)
        simple_goals = set(new_goals.keys())
        self.h_resources.take_measures()
        self.h_duration.take_measures()
        minerals = self.h_resources.h(new_state,new_goals)
        vespin = self.h_resources.h(new_state,new_goals, lambda x: x.vespin)
        print(vespin)
        print(minerals)

        #print(self.state)
        #print(new_state)
        #print(new_goals)
        one_end = self.window.get_potential() + self.state.project_h(minerals,vespin)
        second_end = self.window.get_potential() + self.h_duration.LM_Cutting(simple_state,simple_goals)
        #print(self.window.get_potential())
        #print(self.window.a_order)
        print("First end:"+str(one_end))
        print("Second end:" + str(second_end))
        #assert False
        return max(second_end,one_end)





def AstarSearch(game: Game, actions: ActionPool, goals:List[Goal]):
    step = actions.max_duration()
    min = actions.min_duration()
    base = 20000
    """for g in goals:
        base += g.count*step"""
    ub_time = base

    state = game.state
    plan_distance=0
    for g in goals:
        progress = state.check(g)
        if progress <= 0:
            goals.remove(g)
        plan_distance += progress

    bestplan = MockPlan(0,plan_distance)
    stop_signal = False
    #while (not stop_signal) and (type(bestplan) is MockPlan):
    print("----------------------------------------------------------------------")
    bestplan,stop_signal = AStarDFS(game, goals, 0, ub_time, 0, plan_distance)
    ub_time += base
    return bestplan

sequence =["Mutate Hatchery","Mutate Spawning Pool","Mutate Lair","Mutate Spire","Mutate Mutalisk"]


def AStarDFS(game: Game, goals, current_time, ub_time, depth: int, ub_distance):

    if game.max_depth < depth:
        game.max_depth = depth
    #print(game.window)
    #print("Some Word:"+str(game.state))
    check = 0
    """global sequence
    for i in range(min(len(game.window.a_order), len(sequence))):
        if game.window.a_order[i].name == sequence[i]:
            check += 1"""
    #print(ub_time)
    #print(game.window.a_order)
    game.node_count += 1
    besttime=ub_time

    depth2=depth+1
    goal_distance = game.update(goals) #distance of every childnode  <= goal_distance
    bestsignal = True
    best_distance = goal_distance
    bestplan = MockPlan(ub_time, best_distance)

    if game.is_over_bounds():
        print("Dosáhli jsme maximálních hranice")
        game.finished_branches += 1
        return MockPlan(ub_time,goal_distance),True

    """if (depth == 6 ):
        print("Hloubka...")
        return MockPlan(ub_time,goal_distance),True#něco co není potenciál"""

    plan_act = game.action_pool
    if len(plan_act) == 0:
        print("Slepá ulička")
        game.finished_branches += 1
        return MockPlan(ub_time, goal_distance),True

    potential = game.potential_end(goals)
    if (potential >= ub_time):
        print("Limitní čas...")
        game.finished_branches += 1
        return MockPlan(potential,goal_distance),False #něco co není potenciál

    if goal_distance <= 0:
        print("Vyhráli jsme!")
        plan = game.get_plan(goal_distance)
        print(plan)
        print(game.window.a_order)
        print(game.state)
        #assert False
        game.finished_branches +=1
        game.good_branches += 1
        #assert game.good_branches < 7
        return plan, True
    goals2 = goals


    #planovatelné akce od tohoto okamžiku
    #print(current_time)

    #print(game.window.a_order)

    for a in plan_act.actions:

        z = time.time()
        if not game.state.is_plannable(a):
            print("Unplannable"+str(a))
            continue
        else:
            print("Začíná"+str(a))
        #print(current_time)
        #print(game.state)
        assert int(game.state.unaries["Larva_Timer"]) >= 0

        new_current_time = game.plan_next_action(a)

        #print(game.state)
        #print("bf/af")
        finished_actions = game.refresh(new_current_time)
        game.finish_actions(finished_actions)
        w = time.time()
        game.hot_time += (w - z)
        #print(game.state)
        #print(game.state.unaries)
        assert game.state.minerals >=0
        print("Dem dovnitř!"+ str(a)+"Depth:"+str(depth))

        plan,signal = AStarDFS(game, goals2, new_current_time, besttime,depth2,best_distance)
        if besttime > plan.time :
            print("Changing best plan"+str(depth)+"-"+str(besttime)+str(bestplan)+"/"+str(plan))
            bestplan = plan
            besttime = plan.time
        bestsignal = bestsignal and signal

        #print(game.state.unaries)
        game.reverse(current_time)

        print("Dem ven! - " + str(current_time) + str(a))
    return bestplan,bestsignal