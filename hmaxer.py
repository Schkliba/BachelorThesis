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
        self.parent = action.preconditions()[0]

    def preconditions(self):
        return self.inner_action.preconditions()
    def __repr__(self):

        return self.name
    def preconditions_cost(self):
        return self.inner_action.unary_cost

    def set_parent(self, parent):
        self.parent = parent

    def preconditions_req(self):
        return self.inner_action.prereq
    def effects(self):
        return self.inner_action.effect
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
        self.variables = set()
        self.by_action = {}
        self.metric = metric
        self.measures={}
        self.by_req = {}

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
        self.variables.update(action.preconditions())
        for p in action.preconditions():
            if p in self.by_req:
                self.by_req[p] += [node]
            else:
                self.by_req[p] = [node]
        for e in action.effects():
            self.variables.add(e)
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


import priorityq
class ParallelHeuristic(JustificationGraph):

    def __init__(self,and_f, or_f = min, measure=lambda x: x.duration):
        super().__init__(measure)
        self.and_f = and_f
        self.or_f = or_f
        self.heuristic_vals = {}

    def h_ci(self,start_variables,goal_variables):
        queue = priorityq.MinPriorityQueue()
        print("začnu!")
        for v in self.variables:
            if v in start_variables:
                self.heuristic_vals[v] = 0
                queue.insert((0,v))
            else:
                self.heuristic_vals[v] = math.inf
                queue.insert((math.inf,v))
        U = {}
        for a in self.by_action:
            U[a] = len(self.by_action[a].preconditions())
        while not queue.isEmpty():
            h,v = queue.pop()
            #print(v+"/"+str(h))

            if v in self.by_req:
                act_nodes = self.by_req[v]
            else:
                act_nodes = []

            for action in act_nodes:
                hn = h + self.measure(action)
                U[action.name] -= 1
                if U[action.name] == 0:
                    for e in action.effects():
                        if hn < self.heuristic_vals[e]:
                            self.heuristic_vals[e] = hn
                            #if e in self.by_req:
                             #   for c in self.by_req[e]:
                             #       U[c.name] += 1
                        queue.insert((hn,e))
        ret_val = -math.inf #TODO: Not hardcode
        for g in goal_variables:
            ret_val=self.and_f(ret_val,self.heuristic_vals[g])
        return ret_val

    def h(self, state_variables,goal_variables):
        return self.h_ci(state_variables,goal_variables)
        """self.heuristic_vals = {}
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
        return h"""


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

def select_most_best(possible_parents,h):
    max_val = - math.inf
    selected_parent = None
    #print("parent_select")
    for p in possible_parents:
        #print(p)
        #print(h[p])
        if p in h and h[p] > max_val:
                selected_parent = p
                max_val = h[p]
    return selected_parent

class LLBHeuristic(ParallelHeuristic):

    def __init__(self,and_f, or_f = min, metric = lambda x:x.duration ):
        super().__init__(and_f,or_f,metric)
        self.select_func = select_most_best
        self.measures = {}
        self.parents = {}
        self.edges = {}

    def LM_Cutting(self,state_variables,goal_variables): #TODO infinite loop. third area exists
        #print("cutting")
        h_lm = 0
        ha = self.h(state_variables, goal_variables)
        while ha > 0:
            #print("looped")

            #print(ha)
            #TODO: main representaant selection - building graph
            self.buildGraph(state_variables,goal_variables)
            V_g = self.target_search(goal_variables)
            #print(V_g)
            V_s = self.source_search(V_g)
            landmark = self.find_cut(V_g, V_s)
            #print(landmark)
            #print(self.heuristic_vals)
            #print(self.variables)
            #print(self.by_action.keys())
            #print(state_variables)
            #

            #print(V_s)
            #print(V_g)
            assert landmark != []
            h_lm += self.adjust_for(landmark)
            ha = self.h(state_variables, goal_variables)

        #print(self.heuristic_vals)
        #return landmark
        return h_lm

    def buildGraph(self, start_variables, goal_varibales):
        self.edges.clear()
        for name,action in self.by_action.items():
            parent = self.select_func(action.preconditions(), self.heuristic_vals)
            self.parents[action.name] = parent
            for e in action.effects():
                if e not in self.edges:
                    self.edges[e] = []
                self.edges[e].append((parent, action))

        for v_s in start_variables:
            if v_s not in self.edges:
                self.edges[v_s] = []
            self.edges[v_s] += [("start", None)]
        parent = self.select_func(goal_varibales, self.heuristic_vals)
        self.edges["goal"] = [(parent, None)]



    """def buildGraph(self, start_variables, goal_varibales):
        for variable in self.variables:
            nodes = self.by_effects[variable]
            preconds=[]
            actions = []
            for n in nodes:
                print(n.name)
                preconds+=n.preconditions()
            print(variable)
            parent = self.select_func(preconds,self.heuristic_vals)

            print(preconds)
            for n in nodes:
                if parent in n.preconditions():
                    actions += [n]
            self.parents[variable] = (parent,actions)
        for v_s in start_variables:
            self.parents[v_s] = ("start",[])
        parent = self.select_func(goal_varibales,self.heuristic_vals)
        self.parents["goal"] = (parent,[])
    """
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

    def find_cut(self, V_g, V_s):

        сut_actions = []
        for variable in V_g:
            #print("changing variable")

            edges = self.edges[variable]
            #print(variable)
            #print(p_var)
            for parent,action in edges:
                if parent in V_s:
                    сut_actions += [action]

        return сut_actions
    def source_search(self, V_g):

        h_max = 0
        sufficing_actions = self.variables - set(V_g)
        return sufficing_actions

    def target_search(self, goals):

        queue = ["goal"]  # goals jsou jen stringy
        outset = []
        visited = set()

        while not len(queue) == 0:
            variable = queue.pop(0)
            if variable in visited:
                continue
            visited.add(variable)
            edges = self.edges[variable]
            print(edges)
            for parent, action in edges:
                if action is not None:
                    distance = self.measure(action)
                else:
                    distance = 0

                if distance == 0:
                    queue += [parent]
                    outset.append(parent)
        return outset
    """def target_search(self, goals):

        queue = ["goal"] # goals jsou jen stringy
        outset = []
        visited = set()
    

        while not len(queue) == 0:
            action_edge = queue.pop(0)
            if action_edge in visited:
                continue
            visited.add(action_edge)
            distance = self.measure(action_edge)
            if distance == 0:
                prec = self.parents[action_edge.name]
                outset += [prec]
                queue += self.by_effects[prec]
        return outset"""


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
        self.take_measures()

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