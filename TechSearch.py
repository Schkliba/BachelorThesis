
import xml.etree.ElementTree as ET
#pouze boolovksé predikáty
#bez podpory funkcí

class TechTreeReader:
    def extract_array(self, root, catch):
        return root.findall(catch)

    def make_literal(self,root):
        name = root.text
        type = "object"
        return Literal(name,type)

    def make_action(self,root):
        name = root.get("name")
        preposition = [self.make_predicate(con)for con in self.extract_array(root.find("conditions"),"condition")]
        postposition = [self.make_predicate(con)for con in self.extract_array(root.find("effects"),"effect")]
        params = [par.text for par in self.extract_array(root.find("params"),"param")]
        return Action(name,params,preposition,postposition)

    def make_predicate(self,root):
        name = root.get("name")
        polarity = root.get("value") == "true"
        literals = root.findall("literal")
        lits=[]
        for l in literals:
             lits += [self.make_literal(l)]
        return Predicate(name,lits,polarity)

    def make_gnd_predicate(self,root):
        name = root.get("name")
        polarity = root.get("value") == "true"
        literals = root.findall("literal")
        lits=[]
        for l in literals:
             lits.append(self.make_literal(l))
        return GroundedPredicate(name,lits,polarity)

    def make_init(self,root):
        state = dict()
        literals = [self.make_literal(lit) for lit in root.findall("literal")]
        conditions = root.findall("predicate")

        for cnd in conditions:
            pred = self.make_gnd_predicate(cnd)
            if pred.name not in state:
                state[pred.name] = []
            state[pred.name].append(pred)

        return (state,literals)

    def get_realm(self,filename):
        tree = ET.parse(filename)
        root = tree.getroot()

        xliterals = root.findall("literal")
        xactions = root.findall("action")
        xgoals = root.find("goals")
        xinit = root.find("init")

        made = self.make_init(xinit)
        realm = Realm(made)
        for lit in xliterals:
            made = self.make_literal(lit)
            realm.register_literal(made)
        for ac in xactions:
            made = self.make_action(ac)
            realm.register_action(made)
        for goal in xgoals.findall("goal"):
            made = self.make_gnd_predicate(goal)
            realm.register_goal(made)
        print("Everything ready! Grounding actions!")
        realm.ground_actions()
        print("Actions grounded!")
        return realm

class Realm:
    def __init__(self, init):
        state,literals = init
        self.state = state
        self.existing_literals = literals
        self.goals = []
        self.actions = dict()

    def register_goal(self,goal):

        self.goals.append(goal)

    def register_action(self,action):
        self.actions[action.name] = action

    def register_literal(self,literal):
        self.existing_literals.add(literal)

    def is_predic_true(self,predicate):
        if predicate.name in self.state:
            if predicate in self.state[predicate.name]:
                return True
        return False

    def permits(self,action):
        return action.reached(self)
    def is_predic_false(self,predicate,literals):
        return not self.is_predic_true(predicate,literals)

    def ground_actions(self):
        for act in self.actions:
            self.actions[act].generate_grounded(self)

    def relevant_actions(self,goal):
        ret_value = []
        for act in self.actions:
            ret_value = ret_value + self.actions[act].gnd_resulting_in(goal)
        return ret_value

    def realm_search(self):
        return Simplesearch(self.state,self.goals,self,[],0)

class Literal:
    def __init__(self,name,type):
        self.name = name
        self.type = type

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type
    def __hash__(self):
        return self.name.__hash__()
    def __str__(self):
        return self.name + "("+self.type+")"
    def __repr__(self):
        return self.name + "(" + self.type + ")"

class Predicate:
    def __init__(self,name, params, polarity = True):
        self.name = name
        self.params = params
        self.truth = polarity

    def ground(self,param_map):
        literals = []
        for p in self.params:
            if p.name in param_map:
                literals += [param_map[p.name]]

        return GroundedPredicate(self.name,literals,self.truth)

    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

class GroundedPredicate:
    def __init__(self, name,literals ,truth = True):
        self.name = name
        self.literals = literals
        self.truth = truth

    def has_same_lits(self,other):
        len(self.literals) == len(other.literals)
        for lit in self.literals:
            if lit not in other.literals: return False
        return True
    def satisfied_by(self,state):
        if self.name in state:
            return self in state[self.name]
    def __eq__(self, other):
        #print(str(self) + " vs. "+ str(other))
        return self.truth==other.truth and self.name == other.name and self.has_same_lits(other)
    def __str__(self):
        if self.truth: pol = ""
        else: pol="!"
        return pol+self.name + str(self.literals)
    def __repr__(self):
        return str(self)
    def __not__(self):
        return GroundedPredicate(self.name,self.literals,not self.truth)
class Action:

    def __init__(self, name, params, pre = set(), post = set()):
        self.name = name
        self.param_map = params
        self.precon = pre
        self.postcon = post
        self.gnd_acts = []

    def gnd_resulting_in(self,goal):
        ret_val = []
        for act in self.gnd_acts:
            if act.results_in(goal):
                ret_val+=[act]
        return ret_val


    def generate_grounded(self, realm):
        all_literals = realm.existing_literals
        lit_path = []

        self.grounder(all_literals, self.param_map, lit_path, realm)


    def grounder(self,all_lits,params,path, realm): #FUNGUJE, ALE JE POTŘEBA REWORK (TYPY)!!!!!!!!!!
        if len(path) == len(params):
            param_map = {}
            for i in range(len(params)):
                param_map[params[i]] = path[i]

            gnd_pre = [cond.ground(param_map) for cond in self.precon]
            gnd_post = [eff.ground(param_map) for eff in self.postcon]
            gnd_act = GroundedAction(self,path,gnd_pre,gnd_post)
            print(gnd_act)
            self.gnd_acts += [gnd_act]

        for lit in all_lits:
            if lit not in path:
                new_path= path + [lit]

                self.grounder(all_lits,params,new_path, realm)

class GroundedAction:
    def __init__(self, action,params, precon, postcon):
        self.params = params
        self.action = action
        self.precon = precon
        self.postcon = postcon

    def results_in(self,goal):
        return goal in self.postcon

    def __str__(self):
        out_str = self.action.name + "("
        for index,p in enumerate(self.params):
            if index > 0: out_str += ", "
            out_str += str(p)
        return out_str+")\n"
    def __repr__(self):
        return str(self)

    def reached(self, realm):
        for p in self.precon:
            if not realm.is_predic_true(p): return False
        return True
    def contradicts(self,goals):
        ret = False
        for goal in goals:
            ret = (goal.__not__()) in self.postcon
        return ret

    def apply_on(self, state):
        for p in self.postcon:
            if p.name in state:
                if p not in state[p.name]:  state[p.name].append(p)
            else:
                state[p.name] = [p]
        return state

def Simplesearch(in_state, goals, realm, plan, depth):
    i = 0
    ret_plan = plan
    print(depth)

    cur_goals = goals

    while i < len(cur_goals):
        cur_goal = cur_goals[i]
        if cur_goal.satisfied_by(in_state):
            i += 1
            continue
        feasible_actions = realm.relevant_actions(cur_goal)
        #print("Actions: "+str(feasible_actions))
        if len(feasible_actions) == 0:
            print("Slepá ulička. Není žádná akce pro daný cíl: "+str(cur_goal))
            return []

        goal_plan = []

        for index in range(len(feasible_actions)):
            if feasible_actions[index].contradicts(goals):
                print("Kontradikce: "+str(feasible_actions[index]))
                print("Akce kontradikuje některý goal, nelze použít")
                continue
     #     if feasible_actions[index].reached(in_state):
      #          continue
            new_goals = list(feasible_actions[index].precon)
            new_state = dict(in_state)
            new_state = feasible_actions[index].apply_on(new_state)
            print("Selecting Action: "+str(feasible_actions[index]))
            print("NewGoals: "+str(new_goals))

            cur_plan = Simplesearch(new_state,new_goals,realm,plan+[feasible_actions[index]],depth+1)

            if len(cur_plan) == 0: continue
            if len(goal_plan) > 0 and len(goal_plan)>len(cur_plan):
                goal_plan = cur_plan
            elif len(goal_plan)==0:
                goal_plan = cur_plan

        ret_plan = goal_plan

    return ret_plan

filename = "techtree.txt"
ofilname = "plan.out"
print("Starting up, boss!")
pddl = TechTreeReader()
realm = pddl.get_realm(filename)
plan = realm.realm_search()
planfile = open(ofilname,'w')
if len(plan) == 0:
    print("There's no plan, boss!")
else: print ("Got the plan, boss!")
print(plan)
for p in range(len(plan)-1,-1,-1):
    planfile.write(str(plan[p]))
planfile.close()