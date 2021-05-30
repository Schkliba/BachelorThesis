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
    def __init__(self):
        self.by_effects = {}
        self.measure = lambda x : x.duration
        self.varibales = set()
        self.by_action = {}


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

    def h_max(self, state_variables,goal_variables, measure=lambda x: x.duration):
        print(goal_variables)
        h_max = 0
        self.measure = measure
        for g in goal_variables: #and vrcholy
            if g not in state_variables:
                new_sources = self.by_effects[g]
                little_h = math.inf
                for s in new_sources:  # or search přes akce naplňují preconditions
                    value = self.h_max_search(state_variables, s)
                    little_h = min(little_h, value)
            else:
                little_h = 0
            h_max = max(h_max, little_h)
        return h_max


    def h_max_search(self, state_variables, source):
        if source.visited: #detekce cyklů
            return math.inf
        source.visited = True
        action_measure = self.measure(source.inner_action)
        h_max = 0
        for p in source.preconditions(): #and search přes jednotlivé proconditions

            if p not in state_variables:
                new_sources = self.by_effects[p]
                little_h = math.inf
                for s in new_sources:# or search přes akce naplňují preconditions
                    value = self.h_max_search(state_variables,s)
                    little_h = min(little_h,value)
            else:
                little_h = 0
            h_max = max(h_max,little_h+action_measure)
        source.visited = False
        source.h_max = h_max
        return h_max

    def h_add(self, state_variables,goal_variables, measure=lambda x: x.minerals):
        print(goal_variables)
        h_max = 0
        self.measure = measure
        for g in goal_variables: #and vrcholy
            if g not in state_variables or goal_variables[g] != state_variables[g]:
                new_sources = self.by_effects[g]
                little_h = math.inf
                for s in new_sources:  # or search přes akce naplňují preconditions
                    value = self.h_max_search(state_variables, s)
                    little_h = min(little_h, value)
            else:
                little_h = 0
            h_max = h_max + little_h
        return h_max


    def h_add_search(self, state_variables, source):
        if source.visited: #detekce cyklů
            return math.inf
        source.visited = True
        action_measure = self.measure(source.inner_action)
        h_add = 0
        for p in source.preconditions_numbered(): #and search přes jednotlivé proconditions
            if p not in state_variables:
                new_sources = self.by_effects[p]
                little_h = math.inf
                for s in new_sources:# or search přes akce naplňují preconditions
                    value = self.h_max_search(state_variables,s)
                    little_h = min(little_h,value)
            else:
                little_h = 0
            h_add = h_add+little_h
        h_add += action_measure
        source.visited = False
        source.h_add = h_add
        return h_add
    """
    def restart(self,plannables):
        start = StartNode(in_state)
        self.by_action["Start"] = start
        for p in plannables:
            self.by_action[p].arcNodes(start,self.by_action[p],"starterpack","r")

    def LM_Cutting(self):
        V_star = self.target_search()
        #V_0 = self.reachability_search(V_star)
        landmark = self.find_cut(V_star,None)

    def find_cut(self, V_star, V_0):
        lm = set()
        for node in V_star:
            h_max = 0
            potential_lm = set()
            for edge in node.outgoing:
                distance = self.measure(edge)
                if h_max < distance:
                    h_max = distance
                    potential_lm = {edge}
                elif h_max == distance:
                    potential_lm.add(edge)
            lm = lm.union(potential_lm)

    def target_search(self):

        queue = self.by_action["Goal"].incoming.copy() #goals jsou jen stringy
        outset = {self.by_action["Goal"]}
        while not len(queue) == 0:
            edge = queue.pop(0)
            distance = self.measure(edge)
            if distance == 0:
                source,target,resource,tFyp = edge
                addition = source.incoming.copy()
                outset.add(source)
                queue += addition
        return outset

    def reachability_search(self, target_set):

        queue = self.by_action["Start"].ourgoing.copy()  # goals jsou jen stringy
        outset = {self.by_action["Start"]}
        while not len(queue) == 0:
            edge = queue.pop(0)
            source, target, resource, typ = edge
            if target not in target_set:
                    addition = source.incoming.copy()
                    outset.add(source)
                    queue = addition + queue

        return outset"""
