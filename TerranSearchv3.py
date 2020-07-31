#Naive implementation
# workers don't need to move
# units are bound by population limit

# thrifty algorithm: if there are resources, they are going to be spent
# two timers - vespin and minerals
import copy
from decimal import *
from fractions import *
import math
from typing import List
from actions import *
from ActionState import Status

getcontext().prec = 28 #počet decimálních míst na které se implicině zaokrouhluje

class Goal:
    def __init__(self, name,count,weight = 1):
        self.name = name
        self.weight = weight
        self.count = count


class Status:

    def __init__(self,minerals, vespin, unaries, workers, ves_rat, min_rat, max_worker_add):
        self.minerals = Fraction(minerals).limit_denominator()
        self.vespin = Fraction(vespin).limit_denominator()
        self.unaries = unaries
        self.VR = Fraction(ves_rat).limit_denominator()
        self.MR = Fraction(min_rat).limit_denominator()
        self.max_workers = max_worker_add + workers

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
            return (goal.count - self.shadow[goal.name])*goal.weight
        else: return goal.count * goal.weight

    def unplan_action(self, action):
        print("Unplanning: " + str(action))
        self.minerals +=Fraction(action.minerals)
        self.vespin += Fraction(action.vespin)
        self.idle_workers += action.workers
        for c in action.unary_cost:
            self.unaries[c] += action.unary_cost[c]
        for b in action.burrow:
            self.unaries[b] += action.burrow[b]
        print("shadow1:" + repr(self.shadow))
        for e in action.effect:
            self.shadow[e] -= action.effect[e]
        print("shadow2:" + repr(self.shadow))

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
        self.minerals -= Fraction(action.minerals)
        self.vespin -= Fraction(action.vespin)
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

    def is_plannable(self,action: Action):
        if (self.minerals < action.minerals or self.vespin < action.vespin) and\
                (self.unaries["Worker"] < 1):
            return False

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

    def waited(self,passed_time, unit_number):
        ##TODO:Worker Manager
        self.minerals += self.wait_minerals(passed_time,unit_number)
        self.vespin += self.wait_vespin(passed_time,unit_number)

    def wait_minerals(self,passed_time, unit_number):
        minerals = (self.MR * unit_number) * Fraction(passed_time)
        minerals.limit_denominator()
        return minerals

    def wait_vespin(self,passed_time, unit_number):
        vespin =(self.VR * unit_number) * Fraction(passed_time)
        vespin.limit_denominator()
        return vespin

    def relapsed(self,passed_time, unit_number):
        self.minerals -= Fraction(self.MR * unit_number) * Fraction(passed_time)
        self.vespin -= Fraction(self.VR * unit_number)* Fraction(passed_time)

    def project(self, minerals, vespin, unit_name = "Worker"): #TODO prejktování pokud jsou využití všichni dělníci
        if minerals <= self.minerals:
            mineral_time = 0
        else:
            mineral_time = Decimal(float((Fraction(minerals)-self.minerals)/(self.MR * self.unaries[unit_name])))
            mineral_time = mineral_time.quantize(Decimal('1.'), rounding=ROUND_UP).to_integral_exact()
            print("Projected time:" + str(self.unaries[unit_name]))
        if vespin <= self.vespin:
            vespin_time = 0
        else:
            vespin_time = Decimal(float((Fraction(vespin)-self.vespin)/(self.VR * self.unaries[unit_name])))
            vespin_time = vespin_time.quantize(Decimal('1.'), rounding=ROUND_UP).to_integral_exact()
        if vespin_time < mineral_time:
            return mineral_time
        else:
            return vespin_time

    def project_h(self, minerals, vespin):
        #infinity if too much or 0
        if self.minerals < minerals:
            mineral_time = Decimal(float((Fraction(minerals) - self.minerals) / (self.MR * self.max_workers)))
            mineral_time = mineral_time.quantize(Decimal('1.'), rounding=ROUND_DOWN).to_integral_exact()
        else:
            mineral_time = 0
        if self.vespin < vespin:
            vespin_time = Decimal(float((Fraction(vespin) - self.vespin) / (self.VR * self.max_workers)))
            vespin_time = vespin_time.quantize(Decimal('1.'), rounding=ROUND_DOWN).to_integral_exact()
        else:
            vespin_time = 0
        if vespin_time < mineral_time:
            return mineral_time
        else:
            return vespin_time

class Plan:
    def __init__(self,timeline):
        self.plan = []
        for a in timeline:
            z = copy.deepcopy(a)
            z.finished = True
            self.plan += [z]

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
        self.time_line.add_action(act)
        self.a_order.append(act)

    def plan_action(self, act: ScheduledAction):
        self._plan_action(act)
        self.time = act.start_time
        return act

    def plan_finished_action(self, act: ScheduledAction): #TODO: Je potřeba zavolat finish
        self._plan_action(act)
        self.time = act.end_time
        return act

    def get_potential(self):
        if (len(self.time_line)>1):
            return self.time_line[len(self.time_line)-1].end_time
        else: return 0

    def get_plan(self):

        return Plan(self.time_line)

    def unplan_action(self, action: ScheduledAction):
        self.time_line.delete(action)
        self.a_order.remove(action)
        self.time = action.start_time

    def unplan_last(self):
        if len(self.a_order)<1: return None
        action = self.a_order[len(self.a_order)-1]
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
        for i in range(len(self.time_line)-1, -1, -1):
            if self.time_line[i].end_time <= time:
                self.last_done = i
                break
            opened_actions += [self.time_line[i]]

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

class Game:

    def __init__(self, init_state: Status, actions: ActionPool):
        self.window = PlanningWindow()
        self.w_calendar = {}
        self.state = init_state
        self.action_pool = actions
        self.action_pool.connect(self.state)

    def CT(self):
        return self.window.time

    def unplan_last(self):
        action = self.window.unplan_last()
        print("Last")
        if action.finished: self.state.undo_action(action)
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
        return plan_distance, minerals, vespin

    def update(self,goals):
        self.action_pool.refresh()
        return self.goal_metrics(goals)




    def planable_actions(self):
        assert self.action_pool.plannable is not None
        return self.action_pool.plannable

    def refresh(self, old_time):
        print("Timeshift: "+str(old_time)+"/"+str(self.CT()))
        assert old_time <= self.CT()
        self.refresh_calendar(self.CT(),old_time)
        print("Akce: "+ repr(self.window.time_line))
        return self.window.finish_everything_prior(self.CT())

    def refresh_calendar(self, new_time,old_time):
        #print(str(self.w_calendar) + " --- " + str(old_time)+"/"+str(new_time))
        times = self.w_calendar.keys()
        times = sorted(times, reverse=False)
        ct = old_time
        for time_t in times:
            if (time_t >= old_time) and time_t<=new_time:
                #print(time_t)
                self.state.waited(time_t-ct, self.w_calendar[ct])
                ct = time_t
        self.state.waited(new_time - ct, self.w_calendar[ct])
        assert (self.state.minerals >= 0)

    def finish_actions(self,actions):

        for a in actions:
            a.finish = True
            self.state.end_action(a)

    def time_shift(self, new_time):
        self.window.time = new_time

    def plan_next_action(self, action: Action):

        surplus_time = self.state.project(action.minerals, action.vespin)
        sch_a = action.schedule(self.CT())
        sch_a.add_time(surplus_time)
        pointA = int(sch_a.start_time-sch_a.surplus_time)
        pointB = int(sch_a.start_time)
        self.window.plan_action(sch_a)
        self.w_calendar[pointA] = self.state.unaries["Worker"]
        self.state.start_action(sch_a)
        self.w_calendar[pointB] = self.state.unaries["Worker"]
        return self.CT() #TODO:

    def plan_finished_action(self, action: Action):
        surplus_time = self.state.project(action.minerals, action.vespin)
        sch_a = action.schedule(self.CT())
        sch_a.add_time(surplus_time)
        self.window.plan_finished_action(sch_a)
        pointA = int(sch_a.start_time - sch_a.surplus_time)
        pointB = int(sch_a.start_time)
        self.w_calendar[pointA] = self.state.unaries["Worker"]
        self.state.start_action(sch_a)
        self.w_calendar[pointB] = self.state.unaries["Worker"]
        return self.CT()

    def first_finished_time(self):
        return self.window.first2finish()

    def reverse(self,time): #finished action

        old_time = self.CT()
        actions = self.window.rewind_to(time)
        for a in actions:
            if a.start_time <= time:  # multiple undoing
                if a.finished:
                    self.state.undo_action(a)
                    a.finished = False
            else:
                self.state.unplan_action(a)
                self.window.unplan_action(a)

        self.relapse_through_calendar(time, old_time)


    def relapse_through_calendar(self, time, current_time):
        print(str(self.w_calendar) + " --- "+ str(current_time))
        times = self.w_calendar.keys()
        times = sorted(times, reverse= True)
        ct = current_time
        for time_t in times :
            if time_t > current_time: del self.w_calendar[time_t]
            elif (time_t >= time):
                self.state.relapsed(ct - time_t, self.w_calendar[time_t])
                if time_t != time: del self.w_calendar[time_t]
                ct = time_t


    def get_plan(self, distance):
        #print (self.state.unaries)
        return self.window.get_plan()

    def potential_end(self, minerals, vespin):
        return self.window.get_potential() + self.state.project_h(minerals,vespin)

def betterplan(planA, planB):
    print("A:"+str(planA.time)+" B:"+str(planB.time))
    return planA.time <= planB.time



def AstarSearch(game: Game, actions: ActionPool, goals:List[Goal]):
    step = actions.max_duration()
    min = actions.min_duration()
    base = 0
    for g in goals:
        base += g.count*step
    ub_time = 1 + base
    print("Biiitch"+str(ub_time))
    state = game.state
    plan_distance=0
    for g in goals:
        progress = state.check(g)
        if progress <= 0:
            goals.remove(g)
        plan_distance += progress

    bestplan = MockPlan(0,plan_distance)

    #while type(bestplan) == MockPlan:
    print(game.state)
    bestplan = AStarDFS(game, goals, 0, ub_time, 4, plan_distance)
    ub_time += base
    return bestplan


def AStarDFS(game: Game, goals, current_time, ub_time, depth: int, ub_distance):

    print(current_time)
    besttime=ub_time
    depth2=depth-1
    goal_distance, minerals_vol, vespin_vol = game.update(goals) #distance of every childnode  <= goal_distance

    best_distance = goal_distance
    bestplan = MockPlan(ub_time, best_distance)
    if goal_distance <= 0:
        print("Vyhráli jsme!")
        return game.get_plan(goal_distance)

    #if (depth <= 0 ):
    #    print("Limitní čas...")
    #    return MockPlan(ub_time,goal_distance)#něco co není potenciál

    potential = game.potential_end(minerals_vol,vespin_vol)
    if (potential >= ub_time):
        print("Limitní čas...")
        return MockPlan(potential,goal_distance)#něco co není potenciál


    plan_act = game.action_pool
    goals2 = goals
    #planovatelné akce od tohoto okamžiku
    print(game.action_pool)



    for a in plan_act:

        # finished

        new_current_time = game.plan_finished_action(a)
        finished_actions = game.refresh(current_time)
        game.finish_actions(finished_actions)
        print("Dem dovnitř! f")
        plan = AStarDFS(game, goals2, new_current_time, besttime, depth2,best_distance)
        if besttime > plan.time:
            print("Changing best plan" + str(depth) + "-" + str(besttime) + str(bestplan) + "/" + str(plan))
            bestplan = plan
            besttime = plan.time
        print(game.state.unaries)
        print("Dem ven! f- " + str(current_time))
        game.unplan_last()
        game.reverse(current_time)
        print(game.state.unaries)
        surplus = game.state.project(a.minerals,a.vespin)
        was_in_range = False
        for b in plan_act:
            # cena b < (stav po zaplacení a) + (minerály získáné po dobu trvání a)
            if (b.minerals < (game.state.minerals - a.minerals) + game.state.wait_minerals(a.duration+surplus ,game.state.unaries["Worker"]) and
                b.vespin < (game.state.vespin - a.vespin) + game.state.wait_vespin(a.duration + surplus,
                                                                                           game.state.unaries["Worker"])):
                was_in_range = True
        if was_in_range:
        #unfinished
            new_current_time = game.plan_next_action(a)
            finished_actions = game.refresh(current_time)
            game.finish_actions(finished_actions)
            print("Dem dovnitř!")
            plan = AStarDFS(game, goals2, new_current_time, besttime,depth2,best_distance)
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