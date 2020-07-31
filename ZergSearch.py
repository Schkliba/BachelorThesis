#rozdíl mezi MainHatchery a Hatchery
#MainHatchery je jen jedna(virtuální) - v BW existuje jen jeden Upgrade = nemá vliv
#Hatchery je zapůjčená akcí SpawnLarvab = v jeden okamžik nelze genervat více larev než je generátorů
#Virtuální larvy - resource pro kontrolu larev. Do poolu se přidají 3 s každou hatchery.
#Akce postavit jednotku vrací 1 viruální larvu
#Akce SpawnLarva ubírá 1 virtuální larvu
#Problém - individuální hatch pooly
#Řešení - vybírat larvy z různých poolů je (bez mapy) vždy efektivnější, než primárně vypotřebovat jeden.
#Předpokládáme schopnost hráče si to zařídit.
#Naive implementation
# workers are permanent
# workers don't need to move
# units are bound by population limit

# thrifty algorithm: if there are resources, they are going to be spent
# two timers - vespin and minerals
import copy
import math

class Goal:
    def __init__(self, name, count):
        self.name = name
        self.count = count


class ZergStatus:

    def __init__(self,minerals, vespin, unaries, workers, ves_rat, min_rat):
        self.minerals = minerals
        self.vespin = vespin
        self.unaries = unaries
        self.idle_workers = workers
        self.shadow = copy.deepcopy(unaries)
        self.larvas = ZergClock()
        self.VR = ves_rat
        self.MR = min_rat

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        out = "Status"
        out += "\nMinerals:"+str(self.minerals)
        out += "\nVespin:" + str(self.vespin)
        out += "\nUnaries:" + str(self.unaries)
        out += "\nShadow:" + str(self.shadow)
        out += "\n-------------------------------------"
        return out

    def check(self, goal):
        if goal.name in self.shadow:
            print(str(goal.count)+goal.name+str(self.shadow[goal.name]))
            return goal.count <= self.shadow[goal.name]
        else:
            return False

    def unplan_action(self, action):
        print("Unplanning: " + str(action))
        self.minerals +=action.minerals
        self.vespin += action.vespin
        self.idle_workers += action.workers
        for c in action.unary_cost:
            self.unaries[c] += action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]
        for e in action.effect:
            self.shadow[e] -= action.effect[e]


    def undo_action(self,action): #znovu rozplánuje akci
        print("Undoing: " + str(action))
        self.idle_workers -= action.workers
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]
        for e in action.effect:
            if not (e in self.unaries):
                self.unaries[e] = 0
            self.unaries[e] -= action.effect[e]

    def start_action(self,action):
        self.minerals -= action.minerals
        self.vespin -= action.vespin
        self.idle_workers -= action.workers
        print("Startting: "+str(action))
        for e in action.effect:
            if not (e in self.shadow):
                self.shadow[e] = 0
            self.shadow[e] += action.effect[e]
        for c in action.unary_cost:
            self.unaries[c] -= action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] -= action.burrow[b]

    def end_action(self,action):
        self.idle_workers += action.workers
        print("Finishing: " + str(action))
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]
        for e in action.effect:
            if not( e in self.unaries):
                self.unaries[e] = 0
            self.unaries[e] += action.effect[e]

    def is_plannable(self,action):
        for c in action.unary_cost:
            if c not in self.unaries:return False
            if self.unaries[c] < action.unary_cost[c]: return False
        for b in action.burrow:
            if b not in self.unaries: return False
            if self.unaries[b] < action.burrow[b]: return False
        for r in action.prereq:
            if r not in self.unaries: return False
            if self.unaries[r] < action.prereq[r]: return False

        return True

    def waited(self,passed_time):
        #TODO: Worker Manager


        self.minerals += self.MR*passed_time
        print("RMINERALS:" + str(self.minerals) + "/" + str(passed_time))
        assert (self.minerals >= 0)
        self.vespin += self.VR*passed_time

    def relapsed(self,passed_time):
        print("MINERALS1:" + str(self.minerals) + "/" + str(passed_time))
        self.minerals -= self.MR * passed_time
        print("MINERALS2:" + str(self.minerals) + "/" + str(passed_time))
        self.vespin -= self.VR * passed_time

    def project(self, minerals, vespin):
        if minerals <= self.minerals:
            mineral_time = 0
        else:
            mineral_time = (minerals-self.minerals)/self.MR

        if vespin <= self.vespin:
            vespin_time = 0
        else:
            vespin_time = (vespin-self.vespin)/self.VR

        if vespin_time < mineral_time:
            return mineral_time
        else:
            return vespin_time


class ActionPool:
    def __init__(self):
        self.connected = False
        self.ref_state = None
        self.actions = []
        self.automated = []
        self.plannable = []
        self.to_exec = [] #Předpoklad: automatizovaná akce nebrání jiné akci
        self.idle_action = None
        self.unplannable = []

    def __repr__(self):
        out = "["
        for a in self:
            out+=str(a)
        out+="]"
        return out

    def __str__(self):
        return self.__repr__()

    def __iter__(self):
        return self.plannable.__iter__()

    def max_duration(self):
        if len(self.actions) < 1: return 0
        max_duration = self.actions[0].duration
        for a in self.actions:
            if a.duration > max_duration:
                max_duration = a.duration

        return max_duration

    def min_duration(self):
        if len(self.actions)< 1: return 0
        min_duration = self.actions[0].duration
        for a in self.actions:
            if a.duration <  min_duration:
                min_duration = a.duration

        return min_duration

    def register_action(self, action):
        self.actions += [action]

    def register_automated_action(self,action):
        self.automated += [action]

    def connect(self, state):
        self.ref_state = state
        for a in self.actions:
            if state.is_plannable(a):
                self.plannable += [a]

        for a in self.automated:
            if self.ref_state.is_plannable(a):
                self.to_exec.append(a)

    def refresh(self):
        self.plannable= []
        for a in self.actions:
            if self.ref_state.is_plannable(a):
                self.plannable.append(a)

        self.to_exec = []
        for a in self.automated:
            if self.ref_state.is_plannable(a):
                self.to_exec.append(a)

class Plan:
    def __init__(self,timeline):
        self.plan = []
        for a in timeline:
            z = copy.deepcopy(a)
            z.finished = True
            self.plan +=[z]

        if len(self.plan) > 0:
            self.time = timeline[len(timeline)-1].end_time
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
    def __init__(self,time):

        self.time = time

    def __str__(self):
        return "Mock Plan"

class Action:

    def __init__(self,name,workers,minerals,gas,prereq,cost,burrow,duration,effect):
        self.name = name
        self.minerals = minerals
        self.vespin = gas
        self.prereq = prereq#před
        self.unary_cost = cost #zničené suroviny
        self.workers = workers
        self.burrow = burrow #propujčené suroviny
        self.duration = duration
        self.effect = effect #po

    def __str__(self):
        return self.name + "("+str(self.duration)+")"

    def schedule(self,from_t):
        return ScheduledAction(self.name,self.workers, self.minerals,self.vespin,self.prereq,self.unary_cost,
                               self.burrow,self.duration,self.effect,from_t)


class ScheduledAction(Action):

    def __init__(self,name, workers, minerals, gas, prereq, cost, burrow, duration, effect, start_time):
        super().__init__(name, workers, minerals, gas, prereq, cost, burrow, duration, effect)
        self.start_time = start_time
        self.end_time = start_time+duration
        self.surplus_time = 0
        self.finished = False

    def add_time(self, time):
        self.surplus_time = time
        self.start_time += self.surplus_time
        self.end_time += time

    def __eq__(self, other):
        return (self.name == other.name) and (self.start_time == other.start_time) and (self.duration == other.duration) and (self.finished == other.finished)

    def __str__(self):
        return str(self.name) +" ("+str(self.start_time)+";"+str(self.end_time)+str(self.finished)+")"

class Timeline: #objekt pro držení pořadí akcí podle času ukončení

    def __init__(self, type):
        self.actions = [] #TODO iplementace jako strom
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



class PlanningWindow: #ukládání plánu v časové souvislosti

    def __init__(self, timeline=Timeline("ef")):
        self.time = 0
        self.last_done = -1
        self.finish_time = 0
        self.time_line = timeline#invariant: akce s menším indexem končí dřív
        self.a_order = [] #ukládá akce v pořadí v němž byly naplánovány. tj. řazení dle času začátku

    def plan_action(self, act):
        self.time_line.add_action(act)
        self.a_order.append(act)
        self.time = act.start_time
        return act

    def plan_finished_action(self, act): #TODO: Je potřeba zavolat finish
        self.time_line.add_action(act)
        self.a_order.append(act)
        self.time = act.end_time
        return act

    def get_potential(self):
        if (len(self.time_line)>1):
            return self.time_line[len(self.time_line)-1].end_time
        else: return 0

    def get_plan(self):

        return Plan(self.time_line)

    def unplan_action(self, action):
        self.time_line.delete(action)
        self.a_order.remove(action)
        self.time = action.start_time

    def unplan_last(self):
        if len(self.a_order)<1: return None
        action = self.a_order[len(self.a_order)-1]
        #self.time = action.start_time
        self.time_line.delete(action)
        self.a_order.remove(action)
        return action

    def __str__(self):
        return str(self.time_line)

    def first2finish(self): #vrací

        if not(self.last_done+1 < len(self.time_line)): return self.time

        return self.time_line[self.last_done+1].end_time

    def rewind_to(self, time):
        opened_actions = []
        self.time = time

        #if time == 0:
         #   self.last_done = -1
           # opened_actions = self.time_line
            #for a in opened_actions: a.f
          #  return opened_actions
        for i in range(len(self.time_line)-1, -1, -1):

            opened_actions += [self.time_line[i]]
            #self.time_line[i].finished = False
            if self.time_line[i].end_time < time:
                self.last_done = i
                break

        return opened_actions

    def finish_everything_prior(self,time):
        finish_list = []
        if time < self.time: raise RuntimeError("Action Finishing: Cannot go back in time!")

        for i in range(len(self.time_line)):
            a=self.time_line[i]
            if a.end_time <= time and not a.finished:
                finish_list += [a]
                a.finished = True
                self.last_done = i

        self.time = time
        return finish_list

#limits imposed in state
#How to decide whichone creates?
#ASSUMPTION All bases are the same (in terms of position)
#ASSUMPTION
class FacilityStart:
    def __init__(self, inception_time):
        self.time = inception_time
class FacilityNext:
    def __init__(self, time, previous):
        self.time = time
        self.prev = previous

class ZergClock:
    def __init__(self, state, name = "Larva", facility = "Base", limit = 3, time = 60):
        self.state = state
        self.name = name
        self.fac = facility
        self.duration = time
        self.cur_time = 0
        self.fac_tm = []
        self.limit = limit

    def check_facilities(self, time):
        if self.base in self.state.unaries:
            count = self.state.unaries[self.base]
            assert (len(self.fac_tm) <= count)
            if len(self.fac_tm) < count:
                self.fac_tm.append(time)
                self.state[self.name+self.fac+len(self.fac_tm)] = self.limit

    def update(self, time):
        for i in range(len(self.fac_tm)):
            name = self.name+self.fac+len(self.fac_tm)
            if 
                if self.state.unaries[name] > 0:


class ZergGame:
    def __init__(self, init_state, actions):
        self.window = PlanningWindow()
        self.state = init_state
        self.action_pool = actions
        self.action_pool.connect(self.state)

    def CT(self):
        return self.window.time

    def unplan_last(self):
        action = self.window.unplan_last()
        if action.finished: self.state.undo_action(action)
        self.state.unplan_action(action)

    def update(self,goals):
        self.action_pool.refresh()
        for g in goals:
            if not self.state.check(g):
                return False
        return True

    def automated_actions(self):
        return self.action_pool.to_exec

    def planable_actions(self):
        assert self.action_pool.plannable is not None
        return self.action_pool.plannable

    def refresh(self, old_time):
        print(str(old_time)+"/"+str(self.CT()))
        assert old_time <= self.CT()

        #print (self.state.minerals)
        #print(self.state.idle_workers)
        self.state.waited(self.CT()-old_time)
        print("Akce: "+ repr(self.window.time_line))
        return self.window.finish_everything_prior(self.CT())

    def finish_actions(self,actions):

        for a in actions:
            a.finish = True
            self.state.end_action(a)

    def time_shift(self, new_time):
        self.window.time = new_time

    def plan_next_action(self, action):

        surplus_time = self.state.project(action.minerals, action.vespin)
        sch_a = action.schedule(self.CT())
        sch_a.add_time(surplus_time)
        self.window.plan_action(sch_a)
        self.state.start_action(sch_a)

        return self.CT() #TODO:

    def plan_finished_action(self, action):

        surplus_time = self.state.project(action.minerals, action.vespin)
        sch_a = action.schedule(self.CT())
        sch_a.add_time(surplus_time)
        self.window.plan_finished_action(sch_a)
        self.state.start_action(sch_a)

        return self.CT()

    def first_finished_time(self):
        return self.window.first2finish()

    def reverse(self,time): #finished action
        print(time)
        self.state.relapsed(self.CT()-time)
        actions = self.window.rewind_to(time)

        for a in actions:
            if a.start_time<=time: #multiple undoing
                if a.finished:
                    self.state.undo_action(a)
                    a.finished = False
            else:
                self.state.unplan_action(a)
                self.window.unplan_action(a)

    def get_plan(self):
        #print (self.state.unaries)
        return self.window.get_plan()

    def potential_end(self):
        return self.window.get_potential()

def betterplan(planA, planB):
    print("A:"+str(planA.time)+" B:"+str(planB.time))
    return planA.time <= planB.time

def AstarSearch(game, actions, goals):
    step = actions.max_duration()
    min = actions.min_duration()
    ub_time = 1 + step

    state = game.state
    for g in goals:
        if state.check(g):
            goals.remove(g)
    bestplan = MockPlan(0)

    while type(bestplan) == MockPlan:
        max_depth = 70#2*int(math.floor(ub_time / min))
        print("------------------------------------"+str(max_depth)+"--------------------------------")
        print(game.state)
        bestplan = AStarDFS(game, goals, 0, ub_time, max_depth)
        ub_time += step
    return bestplan

def AStarDFS(game, goals, current_time, ub_time, depth):
    print(current_time)
    besttime=ub_time
    bestplan = MockPlan(ub_time)
    depth2=depth-1
    isdone = game.update(goals)
    if isdone:
        print("Vyhráli jsme!")
        return game.get_plan()

    if game.potential_end() >= ub_time:
        print("Limitní čas...")
        return copy.deepcopy(game.get_plan())

    if depth <= 0:
        print("Too deep")
        return bestplan

    plan_act = game.action_pool
    goals2 = copy.deepcopy(goals)
    #planovatelné akce od tohoto okamžiku
    print(game.action_pool)



    for a in plan_act:

        # finished
        new_current_time = game.plan_finished_action(a)
        finished_actions = game.refresh(current_time)
        game.finish_actions(finished_actions)
        print("Dem dovnitř! f")
        plan = AStarDFS(game, goals2, new_current_time, besttime, depth2)
        if besttime > plan.time:
            print("Changing best plan" + str(depth) + "-" + str(besttime) + str(bestplan) + "/" + str(plan))
            bestplan = plan
            besttime = plan.time
        print(game.state.unaries)
        print("Dem ven! f- " + str(current_time))
        game.unplan_last()
        game.reverse(current_time)
        print(game.state.unaries)

        #unfinished
        new_current_time = game.plan_next_action(a)
        finished_actions = game.refresh(current_time)
        game.finish_actions(finished_actions)
        print("Dem dovnitř!")
        plan = AStarDFS(game, goals2, new_current_time, besttime,depth2)
        if besttime > plan.time :
            print("Changing best plan"+str(depth)+"-"+str(besttime)+str(bestplan)+"/"+str(plan))
            bestplan = plan
            besttime = plan.time
        print(game.state.unaries)
        print("Dem ven! - "+str(current_time))

        game.unplan_last()
        game.reverse(current_time)
        print(game.state.unaries)

    return bestplan

action_pool = ActionPool()
action_pool.register_action(Action("Build Zergling", 1, 50, 0, {}, {"Larva":1}, {}, 100, {"Zergling": 1, "VLarva":1}))
goal = Goal("Pylon", 4)
in_state = ZergStatus(200, 0, {"Base": 1, "VBase": 1, "VLarva": 3}, 5, 0.1, 0.3)
action_pool.connect(in_state)
game = Game(in_state, action_pool)
bestplan = AstarSearch(game, action_pool, [goal], 7000)
print(bestplan)