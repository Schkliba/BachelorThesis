from actions import Action
from typing import List,Dict
import math
class ValueHolder:
    def __init__(self):
        self.max = 0
        self.min = 0
        self.visited = False

    def max_set(self,val):
        self.max = val

    def min_set(self,val):
        self.min = val

class Node:
    def __init__(self, name):
        self.name = name
        self.incoming = []

        self.outgoing = []
        self.visited = False

    def add_inArc(self, edge):
        self.incoming.append(edge)


    def add_outArc(self, edge):
        self.outgoing.append(edge)


class JNode(Node):

    def __init__(self, name,action):
        super().__init__(name)
        self.inner_action = action

    def preconditions(self):
        return self.inner_action.preconditions()
    def __repr__(self):
        return self.name
    def preconditions_cost(self):
        return self.inner_action.unary_cost

    def preconditions_req(self):
        return self.inner_action.prereq

    def preconditions_burrow(self):
        return self.inner_action.burrow
    def prereq(self):
        return self.inner_action.prereq.copy()
    def burrow(self):
        return self.inner_action.burrow.copy()
    def unary_cost(self):
        return self.inner_action.unary_cost.copy()


class GoalNode(Node):
    def __init__(self):
        super().__init__("Goal")

class StartNode(Node):
    def __init__(self):
        super().__init__("Start")



def arcNodes(source, target, resource, type):
        edge = (source, target, resource, type)
        target.add_inArc(edge)
        source.add_outArc(edge)
def outgoing(node):
    return node.outgoing_count



class JustificationGraph:
    def __init__(self,metric):
        self.by_effects = {}
        self.varibales = set()
        self.by_action = {}
        self.metric = metric
        self.measures={}

    def __get_or_make_node(self, name) -> JNode:
        if name not in self.nodes.keys():
            node = JNode(name)
            self.nodes[name] = node
        else:
            node = self.nodes[name]
        return node

    def register_action(self,action: Action):
        node = JNode(action.name,action)
        self.by_action[action.name] = node
        for e in action.effect:
            if e in self.by_effects:
                self.by_effects[e] += [node]
            else:
                self.by_effects[e] = [node]

    def take_measures(self):
        for a, node in self.by_action.items():
            self.measures[a] = self.metric(node.inner_action)

    def measure(self,node):
        return self.measures[node.inner_action.name]

    def construct_edges(self):
        for a, action in self.by_action.items():

            for r in action.prereq():
                req_nodes = self.by_effects[r]
                for n in req_nodes:
                    arcNodes(n,action,r,"r")

            for b in action.burrow():
                bur_nodes = self.by_effects[b]
                for n in bur_nodes:
                    arcNodes(n, action, b, "b")

            for c in action.unary_cost():
                co_nodes = self.by_effects[c]
                for n in co_nodes:
                    arcNodes(n, action, c, "c")



class ParallelHeuristic(JustificationGraph):

    def __init__(self,and_f, or_f = min, measure=lambda x: x.duration):
        super().__init__(measure)
        self.and_f = and_f
        self.or_f = or_f
        self.heuristic_vals = {}

    def h(self, state_variables,goal_variables, ):
        h=0
        self.heuristic_vals = {}
        for g in goal_variables: #and vrcholy
            if g not in state_variables:
                new_sources = self.by_effects[g]
                little_h = math.inf
                for s in new_sources:  # or search přes akce naplňují preconditions
                    value = self.h_search(state_variables, s)
                    little_h = self.or_f(little_h, value)
            else:
                little_h = 0
            h = self.and_f(h, little_h)
            if g in self.heuristic_vals:
                self.heuristic_vals[g] = self.and_f(self.heuristic_vals[g], little_h)
            else:
                self.heuristic_vals[g] = little_h
        return h


    def h_search(self, state_variables, source):
        if source.visited: #detekce cyklů
            return math.inf
        source.visited = True
        action_measure = self.measure(source)
        h = 0

        for p in source.preconditions(): #and search přes jednotlivé proconditions
            if p not in state_variables:
                new_sources = self.by_effects[p]
                little_h = math.inf
                for s in new_sources:# or search přes akce naplňují preconditions
                    value = self.h_search(state_variables,s)
                    little_h = self.or_f(little_h,value)
            else:
                little_h = 0
            h = self.and_f(h,little_h)
            if p in self.heuristic_vals: self.heuristic_vals[p] = self.and_f(self.heuristic_vals[p],little_h)
            else: self.heuristic_vals[p] = little_h
        h += action_measure
        source.visited = False

        return h

class LLBHeuristic(ParallelHeuristic):

    def __init__(self,and_f, or_f = min, metric = lambda x:x.duration ):
        super().__init__(and_f,or_f,metric)
        self.measures ={}

    def LM_Cutting(self,state_variables,goal_variables):

        h_lm = 0

        while self.h(state_variables,goal_variables) > 0:
            print("WOOOOOOOO")
            print(state_variables)
            print(self.heuristic_vals)
            V_star = self.target_search(goal_variables)
            print(V_star)
            landmark = self.find_cut(V_star, None)
            print(landmark)
            h_lm += self.adjust_for(landmark)
            print(self.measures)
        #print(self.heuristic_vals)
        #return landmark
        return h_lm

    def adjust_for(self, landmarks):
        mininimum_cost  = math.inf
        for l in landmarks:
            mininimum_cost = min(self.measures[l.name],mininimum_cost)
        for l in landmarks:
            self.measures[l.name] -= mininimum_cost
        return mininimum_cost


    def get_h(self,node):
        ret_val = 0
        for i in node.preconditions():
            ret_val = self.max(ret_val,self.heuristic_vals[i])
        return ret_val

    def find_cut(self, V_star, V_0):

        h_max = 0

        sufficing_actions = []
        for variable in V_star:
            if h_max < self.heuristic_vals[variable]:
                maybe_actions = self.by_effects[variable]
                sufficing_actions = []
                for a in maybe_actions:
                    distance = self.measure(a)
                    print(a)
                    print(distance)
                    if distance > 0:
                        sufficing_actions += [a]
                        h_max = self.heuristic_vals[variable]

        return sufficing_actions

    def target_search(self, goals):

        queue = [] # goals jsou jen stringy
        outset = list(goals)
        visited = set()
        for g in goals:
            queue +=self.by_effects[g]
        while not len(queue) == 0:
            action_edge = queue.pop(0)
            if action_edge in visited:
                continue
            visited.add(action_edge)
            distance = self.measure(action_edge)
            if distance == 0:
                prec = action_edge.preconditions()
                outset += prec
                for p in prec:
                    queue += self.by_effects[p]
        return outset


class CumulativeHeuristic(JustificationGraph):

    def __init__(self,and_f, or_f = min ,measure=lambda x: x.minerals,own = lambda x,y: x*y):
        super().__init__(measure)
        self.and_f = and_f
        self.or_f = or_f
        self.own = own

    def h(self, state_variables,goal_variables, measure=None):

        h = 0
        temp = self.metric
        if measure is not None:
            self.metric = measure
        for g,count in goal_variables.items(): #and vrcholy

            if g not in state_variables or count > state_variables[g]:

                if g in state_variables:
                    request = count-state_variables[g]
                else:
                    request = count
                new_sources = self.by_effects[g]
                little_h = math.inf
                for s in new_sources:  # or search přes akce naplňují preconditions
                    value = self.h_search(state_variables, s, request)
                    little_h = self.or_f(little_h, value)
            else:
                little_h = 0
            h = self.and_f(h, little_h)
        self.metric = temp
        return h


    def h_search(self, state_variables, source, requested_number):
        #print("source"+str(source.inner_action.name))
        #print(requested_number)
        if source.visited: #detekce cyklů
            return math.inf
        source.visited = True
        action_measure = self.measure(source)
        h = 0
        little_h = math.inf
        for p, count in source.preconditions_cost().items(): #and search přes jednotlivé proconditions
            if p not in state_variables or state_variables[p] < count*requested_number:
                if p in state_variables:
                    cur_count = state_variables[p]
                else:
                    cur_count = 0
                new_sources = self.by_effects[p]
                little_h = math.inf


                for s in new_sources:  # or search přes akce naplňují preconditions

                    effect_c = s.inner_action.get_effect(p)
                    value = self.h_search(state_variables, s, math.ceil((count*requested_number - cur_count)/effect_c))
                    little_h = self.or_f(little_h, value)
            else:
                little_h = self.or_f(little_h, 0)


            h = self.and_f(h, little_h)


        for p, count in source.preconditions_req().items(): #and search přes jednotlivé proconditions
            if p not in state_variables or state_variables[p] < count:
                if p in state_variables:
                    cur_count = state_variables[p]
                else:
                    cur_count = 0
                new_sources = self.by_effects[p]
                little_h = math.inf
                for s in new_sources:# or search přes akce naplňují preconditions
                    effect_c = s.inner_action.get_effect(p)
                    value = self.h_search(state_variables,s,math.ceil((count-cur_count)/effect_c))
                    little_h = self.or_f(little_h,value)
            else:
                little_h = self.or_f(little_h,0)
            h = self.and_f(h, little_h)

        for p, count in source.preconditions_burrow().items():  # and search přes jednotlivé proconditions
            if p not in state_variables or state_variables[p] < count:
                    if p in state_variables:
                        cur_count = state_variables[p]
                    else:
                        cur_count = 0
                    new_sources = self.by_effects[p]
                    little_h = math.inf
                    for s in new_sources:  # or search přes akce naplňují preconditions
                        effect_c = s.inner_action.get_effect(p)
                        value = self.h_search(state_variables, s, math.ceil((count-cur_count)/effect_c)) #necheme překročit optimum, tedy považujeme za prereq
                        little_h = self.or_f(little_h, value)
            else:
                little_h = self.or_f(little_h,0)

            h = self.and_f(h,little_h)

        h += self.own(action_measure, requested_number)
        source.visited = False
        source.h = h
        return h