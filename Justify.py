from actions import Action
from typing import List,Dict
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
        self.outgoing_count = 0
        self.incoming_count = 0
        self.incoming = []
        self.max_count = 0
        self.min_count = 0
        self.current_value = 0
        self.visited = False
        self.default = 0

    def add_inArc(self, edge):
        self.incoming.append(edge)
        self.incoming_count += 1

    def add_outArc(self, edge):
        self.outgoing.append(edge)
        self.outgoing_count += 1
    def get_max_count(self):
        return self.max_count

    def get_min_count(self):
        return self.min_count

    def set_count(self, count):
        self.max_count = count
        self.min_count = count
        self.default = count
        self.outgoing_count = 0

    def is_grower(self):
        for o in self.outgoing:
            source, target, action, typ, val = o
            if typ == "c" and self.max_count > 0:
                return True
        return False

    def recount(self):
            self.max_count = self.default
            self.min_count = self.default
            for o in self.outgoing:
                source, target, action, typ, val = o
                if typ == "c":
                    self.max_count += val.max
                    self.min_count += val.min
            for o in self.outgoing:
                source, target, action, typ, val = o
                if typ == "b":
                    self.max_count += val.max
                    self.min_count = max(self.min_count,val.min)
            for o in self.outgoing:
                source, target, action, typ, val = o
                if typ == "r":
                    self.max_count = max(self.max_count,val.max)
                    self.min_count = max(self.min_count,val.min)

def arcNodes(source, target, action, type):
    val = ValueHolder()
    edge = (source, target,action, type, val)
    target.add_inArc(edge)
    source.add_outArc(edge)

def outgoing(node):
    return node.outgoing_count

class JustificationGraph:
    def __init__(self):
        self.init = None
        self.goal = None
        self.nodes = {}

    def __get_or_make_node(self, name) -> JNode:
        if name not in self.nodes.keys():
            node = JNode(name)
            self.nodes[name] = node
        else:
            node = self.nodes[name]
        return node

    def register_action(self,action: Action):
        print(action.effect)
        for e in action.effect:
            ef_node = self.__get_or_make_node(e)
            for r in action.prereq:
                req_node = self.__get_or_make_node(r)
                arcNodes(req_node,ef_node,action,"r")

            for b in action.burrow:
                bur_node = self.__get_or_make_node(b)
                arcNodes(bur_node,ef_node,action,"b")

            for c in action.unary_cost:
                co_node = self.__get_or_make_node(c)
                arcNodes(co_node,ef_node,action,"c")

    def get_starting_point(self,state):
        root = self.__get_or_make_node("start")
        for n in state:
            done_node = self.nodes[n]
            arcNodes(root,done_node,None,"s")
        self.init = root

    def get_starting_point(self,state):
        root = self.__get_or_make_node("start")
        for n in state:
            done_node = self.nodes[n]
            arcNodes(root,done_node,None,"s")
        self.init = root

    def Filter(self,in_state, goals):
        stated_goals = []

        for g in goals:
            self.nodes[g.name].set_count(g.count)
            stated_goals += [g.name]
        ret_plan = self.filtersearch(in_state,stated_goals,0)
        max_goal_state = {}
        min_goal_state = {}
        # print(self.nodes)
        for n, node in self.nodes.items():
            node.recount()
            if node.max_count > 0:
                max_goal_state[n] = node.max_count
                min_goal_state[n] = node.min_count
        new_state = set()
        new_goals = set()
        for s in in_state:
            if self.nodes[s].is_grower():
                new_goals.add(s)
            else:
                new_state.add(s)
        ret_plan2 = self.filtersearch(new_state, new_goals,0) # není stabilní kvůli designu Tech tree
        # závisí na pořádí, někdy bere Hive, jindy ne.
        ret_plan = ret_plan.union(ret_plan2)
        return max_goal_state, min_goal_state, ret_plan

    def filtersearch2(self, in_state: Dict, goals):
        i = 0
        ret_plan = set([])
        #print(depth)
        queue = [(list(goals),in_state)] #goals jsou jen stringy

        while not len(queue) == 0:
            cur_goal,state = queue.pop(0)
            if cur_goal in in_state:
                continue
            feasible_actions = self.nodes[cur_goal].incoming

            # print("Actions: "+str(feasible_actions))
            if len(feasible_actions) == 0:
                print("Slepá ulička. Není žádná akce pro cíl: " + str(cur_goal))
                return {}

            nessessary_actions = set([])
            self.nodes[cur_goal].recount()
            for index in range(len(feasible_actions)):
                # ve starcraftu se akce nekontradikují

                #     if feasible_actions[index].reached(in_state):
                #          continue
                source, target, action, typ, value = feasible_actions[index]
                #if value.visited: continue
                #target = self.nodes[cur_goal]

                if typ == "b":
                    value.max_set(target.max_count)  # min/max
                    value.min_set(1)
                elif typ == "r":
                    value.max_set(1)
                    value.min_set(1)
                elif typ == "c":
                    print("Ni!!!!!")
                    value.max_set(target.max_count)
                    value.min_set(target.min_count)

                queue = queue + action.preconditions()

                new_state = in_state.union(set(action.postconditions()))

                nessessary_actions.add(action)
                print("Next")
                value.visited = True
                #cur_plan = self.filtersearch(new_state, new_goals, depth + 1)

            i+=1
            ret_plan = ret_plan.union(nessessary_actions)

        return  ret_plan

    def filtersearch(self, in_state: Dict, goals, depth) -> List[Action]:
        i = 0
        ret_plan = set([])
        #print(depth)
        cur_goals = list(goals) #goals jsou jen stringy

        while i < len(cur_goals):
            cur_goal = cur_goals[i]
            if cur_goal in in_state:
                i += 1
                continue
            feasible_actions = self.nodes[cur_goal].incoming

            # print("Actions: "+str(feasible_actions))
            if len(feasible_actions) == 0:
                print("Slepá ulička. Není žádná akce pro cíl: " + str(cur_goal))
                return set([])

            nessessary_actions = set([])
            self.nodes[cur_goal].recount()
            for index in range(len(feasible_actions)):
                # ve starcraftu se akce nekontradikují

                #     if feasible_actions[index].reached(in_state):
                #          continue
                source, target, action, typ, value = feasible_actions[index]
                if value.visited: continue
                #target = self.nodes[cur_goal]

                if typ == "b":
                    value.max_set(target.max_count)  # min/max
                    value.min_set(1)
                elif typ == "r":
                    value.max_set(1)
                    value.min_set(1)
                elif typ == "c":
                    print("Ni!!!!!")
                    value.max_set(target.max_count)
                    value.min_set(target.min_count)

                new_goals = action.preconditions()

                new_state = in_state.union(set(action.postconditions()))

                nessessary_actions.add(action)
                print("Next")
                value.visited = True
                cur_plan = self.filtersearch(new_state, new_goals, depth + 1)
                value.visited = False
                nessessary_actions = nessessary_actions.union(cur_plan)

            i+=1
            ret_plan = ret_plan.union(nessessary_actions)

        return  ret_plan
