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


class JNode:
    def __init__(self, name):
        self.name = name
        self.outgoing = []
        self.actions = []
        self.stop_fail_propagation = False
        self.visited = False
    def justification_actions(self):
        return self.actions
    def add_making_action(self,action):
        self.actions.append(action)

    def add_inArc(self, action, type):
        self.incoming.append(action)

    def add_outArc(self, edge):
        self.outgoing.append(edge)

    def get_max_count(self):
        return self.max_count

    def get_min_count(self):
        return self.min_count


def arcNodes(source, target, action, type):
    #val = ValueHolder()
    #edge = (source, target,action, type, val)
    target.add_inArc(action,type)
    source.add_outArc(action,type)

def outgoing(node):
    return node.outgoing_count

class JustificationGraph:
    def __init__(self):
        self.init = None
        self.goal = None
        self.nodes = {}
        self.actions = []
        self.vspin = False
        self.by_effect = {}

    def __get_or_make_node(self, name) -> JNode:
        if name not in self.nodes.keys():
            node = JNode(name)
            self.nodes[name] = node
        else:
            node = self.nodes[name]
        return node

    def register_action(self,action: Action):
        #print(action.effect)
        self.actions +=[action]
        if action.vespin > 0:
            self.vespin = True
        for e in action.effect:
            ef_node = self.__get_or_make_node(e)
            ef_node.add_making_action(action)
            if e not in self.by_effect:
                self.by_effect[e] = [action]
            else:
                self.by_effect[e] += [action]
            for r in action.prereq:
                req_node = self.__get_or_make_node(r)
            for b in action.burrow:
                bur_node = self.__get_or_make_node(b)
            for c in action.unary_cost:
                co_node = self.__get_or_make_node(c)

    def Filter(self,in_state, goals):
        stated_goals = {}

        for g in goals:
            stated_goals[g.name] = g.count

        count,max_s,valid = self.filtersearch(in_state,stated_goals,0)
        out_state = sum_merge(max_s,in_state)
        relevant_action = []
        out_state["Vespin"] = 1
        for a in self.actions:
            reject = True
            print(a.name)
            for p in a.postconditions():
                if p  in out_state:
                    print("Not")
                    print(p)
                    reject = False

            if not reject:
                relevant_action.append(a)
        pruned_actions = []
        for a in relevant_action:
            reject = False
            for p in a.preconditions():
                if p not in out_state:
                    reject = True
            if not reject:
                pruned_actions.append(a)

        return out_state, pruned_actions


    def filtersearch(self, in_state: Dict, goals, depth) -> List[Action]:

        ret_plan = set()
        signal = True
        h_sum = 0
        max_state = {}
        for g_name, g_count in goals.items(): #jednotlivé and vrcholy
            cur_node = self.nodes[g_name]
            if g_name in in_state and in_state[g_name]>=g_count: #poku je splněno, neřešíme
                continue
            if cur_node.visited: #detekce cyklu
                cur_node.stop_fail_propagation = True
                return math.inf, {}, False

            feasible_actions = cur_node.justification_actions() #chceme jen akce které pomůžou splnit daný subgoal

            # print("Actions: "+str(feasible_actions))
            if len(feasible_actions) == 0:
                print("Slepá ulička. Není žádná akce pro cíl: " + str(g_name))
                return math.inf,{}, False

            """inicializace lokálních OR proměných"""
            goal_actions = set()
            goal_signal = False
            goal_state = {}
            least_actions = math.inf
            for index in range(len(feasible_actions)): #procházení OR vrcholů

                action = feasible_actions[index]
                sub = 0
                if g_name in in_state:
                    sub = in_state[g_name]

                apply_c = math.floor((g_count - sub) / action.effect[g_name]) #výpočet kolikrát musíme uplatni akci pro splnění goalu
                if (g_count - sub) % action.effect[g_name] > 0:
                    apply_c += 1
                #print(action.name)
                #print(apply_c)
                new_goals = {} #výroba nových subgoalů
                for r in action.prereq:
                    subtrack = 0
                    if r in in_state and action.prereq[r] > in_state[r]:
                        subtrack = action.prereq[r] - in_state[r]
                    elif r not in in_state:
                        new_goals[r] =  action.prereq[r]

                for b in action.burrow:
                    subtrack = 0
                    if b in in_state:
                        subtrack = in_state[b]
                    if b not in in_state or (action.burrow[b]*apply_c) > in_state[b]:
                        new_goals[b] = (action.burrow[b]*apply_c) - subtrack
                for c in action.unary_cost:
                    new_goals[c] = (action.unary_cost[c] * apply_c)


                change = {} #dáváme dohromady stav
                for e in action.effect: #TODO: musí být dictionary
                    change[e] = action.effect[e] * apply_c

                new_state = sum_merge(in_state,change)
                #print("New_state:"+str(new_state)+"Now in "+cur_node.name+" Needing "+g_name+" "+str(g_count))
                cur_node.visited = True
                new_h, past_state, new_signal = self.filtersearch(new_state, new_goals, depth + 1)
                cur_node.visited = False
                h_c = apply_c * action.minerals
                if  least_actions>(h_c+ new_h):
                    goal_state = change
                    goal_state = sum_merge(goal_state, past_state)
                    least_actions = h_c+ new_h

                if  least_actions==(h_c+ new_h):
                    goal_state = change
                    goal_state = sum_merge(goal_state, past_state)
            h_sum += least_actions
            max_state = sum_merge(max_state,goal_state)
            signal = signal and goal_signal
            ret_plan = ret_plan.union(goal_actions)

        return h_sum,max_state,signal

    def filtersearch2(self):

        ret_plan = set()
        signal = True
        h_sum = 0
        max_state = {}


        return h_sum,max_state,signal
def sum_merge(dictA, dictB):
    merged = {}
    for k in dictA:
        merged[k] = dictA[k]
    for k in dictB:
        if k not in merged: merged[k] = dictB[k]
        else:
            merged[k] += dictB[k]
    return merged

def max_merge(dictA, dictB):
    merged = {}
    for k in dictA:
        merged[k] = dictA[k]
    for k in dictB:
        if k not in merged: merged[k] = dictB[k]
        else:
            merged[k] = max(merged[k], dictB[k])
    return merged