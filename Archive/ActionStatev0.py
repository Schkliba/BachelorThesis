from decimal import *
from fractions import *
import copy
import math
from typing import List
from actions import *
class Calendar:

    def __init__(self, name, current, in_val):
        self.name = name
        self.timeline = {}
        self.actionline = {}
        self.current_time = current
        self.current_count = in_val
        self.latest = current
        self.shadow = in_val
    def __repr__(self):
        #return str(self.current_count)+":"+str(self.shadow)
        return str(self.timeline)+"<->"+str(self.current_count)+":"+str(self.shadow)

    def __int__(self):
        if type(self.current_count) is not int:
            print(self.name+str(self.current_count))
            raise  ArithmeticError()
        return self.current_count

    def subtract(self, when, number):
        number = int(number)
        if when == self.current_time: self.current_count -= number
        if when in self.timeline: self.timeline[when] -= number
        else: self.timeline[when] = -number
        self.__add_action_line(when)
        self.shadow -= number

    def __add_action_line(self,when):
        if when in self.actionline: self.actionline[when] += 1
        else: self.actionline[when] = 1

    def __undo_action_line(self,when):
        self.actionline[when] -= 1
        if self.actionline[when] == 0:

            del self.actionline[when]
            del self.timeline[when]


    def burrow(self, since, number, duration):
        self.subtract(since,number)
        self.promise(since+duration,number)

    def promise(self, when, number):
        number = int(number)
        if when == self.current_time: self.current_count += number
        if when in self.timeline: self.timeline[when] += number
        else: self.timeline[when] = number
        self.__add_action_line(when)
        self.shadow += number

    def remove_subtraction(self, when, number):
        number = int(number)
        if when == self.current_time: self.current_count += number
        self.shadow += number
        self.timeline[when] += int(number)
        self.__undo_action_line(when)

    def remove_promise(self, when, number):
        number = int(number)
        if when == self.current_time: self.current_count -= number
        self.shadow -= number
        self.timeline[when] -= number
        self.__undo_action_line(when)

    def remove_burrow(self, since, number, duration):
        self.remove_subtraction(since, number)
        self.remove_promise(since + duration, number)


class CountingCalendar(Calendar):
    def __init__(self, name, current, in_val):
        super().__init__(name, current, in_val)

    def get_to(self,new_time):
        if new_time == self.current_time: return
        for time_t in self.timeline:
            if (time_t > self.current_time) and time_t <= new_time:
                self.current_count += self.timeline[time_t]

        self.current_time = new_time

    def return_to(self,new_time):
        if new_time == self.current_time: return
        for time_t in self.timeline:
            if (time_t > new_time) and time_t <= self.current_time:
                self.current_count -= self.timeline[time_t]

        self.current_time = new_time

class WorkingCalendar(Calendar):
    def __init__(self, name, current, in_val, forward_f, return_f):
        super().__init__(name, current, in_val)
        self.return_f = return_f
        self.forward_f = forward_f

    def get_to(self,new_time):
        if new_time == self.current_time: return
        times = self.timeline.keys()
        times = sorted(times, reverse=False)
        old_time = self.current_time
        ct = old_time
        for time_t in times:
            if (time_t > old_time) and time_t <= new_time:
                self.forward_f(time_t - ct, self.current_count)
                self.current_count += self.timeline[time_t]
                ct = time_t
            elif time_t > new_time:
                break
        self.forward_f(new_time - ct, self.current_count)
        #self.current_count += self.timeline[time_t]
        self.current_time = new_time

    def return_to(self,new_time):
        if new_time == self.current_time: return
        times = self.timeline.keys()
        times = sorted(times, reverse=True)
        old_time = self.current_time
        ct = old_time
        for time_t in times:
            if (time_t <= old_time) and time_t > new_time:
                self.return_f(ct - time_t, self.current_count)
                self.current_count -= self.timeline[time_t]
                ct = time_t
            elif (time_t < new_time):
                break
        #self.current_count -= self.timeline[time_t]
        self.return_f(ct-new_time, self.current_count)
        self.current_time = new_time

class Status:

    def __init__(self,minerals, vespin, unaries, workers, ves_rat, min_rat, max_worker_add,ct = 0):
        self.minerals = Fraction(minerals).limit_denominator()
        self.vespin = Fraction(vespin).limit_denominator()
        self.unaries = {}
        self.CT = ct
        for u in unaries:
            self.unaries[u] = CountingCalendar(u,0,unaries[u])
        self.unaries["Worker"] = WorkingCalendar("Worker", 0, workers, self.waited, self.relapsed)
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
        out += "\n-------------------------------------"
        return out

    def check(self, goal):
        if goal.name in self.unaries:
            #print(str(goal.count)+goal.name+str(self.unaries[goal.name].shadow))
            return (goal.count - self.unaries[goal.name].shadow)*goal.weight
        else:
            return goal.count * goal.weight

    def unplan_action(self, action:ScheduledAction):
        #print("Unplanning: " + str(action))
        self.minerals +=Fraction(action.minerals)
        self.vespin += Fraction(action.vespin)
        for e in action.effect:
            amortized, schedule = action.get_effect(e)
            for t, n in schedule.items():
                self.unaries[e].remove_promise(t, n)
        for c in action.unary_cost:
            self.unaries[c].remove_subtraction(action.start_time, action.unary_cost[c])
        for b in action.burrow:
            self.unaries[b].remove_burrow(action.start_time,action.burrow[b],action.duration)

    def plan_action(self,action:ScheduledAction):
        self.minerals -= Fraction(action.minerals)
        self.vespin -= Fraction(action.vespin)
        #print("Startting: "+str(action))
        for e in action.effect:
            amortized, schedule = action.get_effect(e)
            for t, n in schedule.items():
                if e in self.unaries:
                    self.unaries[e].promise(t,n)
                else:
                    self.unaries[e] = CountingCalendar(e,action.start_time,0)
                    self.unaries[e].promise(t,n)
        for c in action.unary_cost:
            self.unaries[c].subtract(action.start_time,action.unary_cost[c])
        for b in action.burrow:
            self.unaries[b].burrow(action.start_time,action.burrow[b],action.duration)


    def is_plannable(self,action: Action):
        if (self.minerals < action.minerals or self.vespin < action.vespin) and\
                (int(self.unaries["Worker"]) < 1):
            return False
        for c in action.unary_cost:
            if c not in self.unaries:
                return False
            if int(self.unaries[c]) < action.unary_cost[c]:
                return False
        for b in action.burrow:
            if b not in self.unaries:
                return False
            if int(self.unaries[b]) < action.burrow[b]:
                return False
        for r in action.prereq:
            if r not in self.unaries:
                return False
            if int(self.unaries[r]) < action.prereq[r]:
                return False

        return True

    def get_to(self,time): #going forward
        #print("Getting to "+str(time))
        for u in self.unaries:
            self.unaries[u].get_to(time)
        self.CT = time

    def return_to(self, time):
        #print("Returning to " + str(time))
        for u in self.unaries:
            self.unaries[u].return_to(time)
        self.CT = time

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
            mineral_time = Decimal(float((Fraction(minerals)-self.minerals)/(self.MR * int(self.unaries[unit_name]))))
            mineral_time = mineral_time.quantize(Decimal('1.'), rounding=ROUND_UP).to_integral_exact()
        if vespin <= self.vespin:
            vespin_time = 0
        else:
            vespin_time = Decimal(float((Fraction(vespin)-self.vespin)/(self.VR * int(self.unaries[unit_name]))))
            vespin_time = vespin_time.quantize(Decimal('1.'), rounding=ROUND_UP).to_integral_exact()
        if vespin_time < mineral_time:
            return int(mineral_time)
        else:
            return int(vespin_time)

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
            return int(mineral_time)
        else:
            return int(vespin_time)
