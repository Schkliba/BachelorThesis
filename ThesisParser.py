import sys
import time
import xml.etree.ElementTree as ET
import TerranSearchv3 as TerranSearch
import Justify as jraph

def MaximumWorkers(volume, innit_w, rate, cost, timespan, production_lines = 1):
    workers = 0
    while ((volume/rate)/(innit_w + workers))+((cost/rate)/(innit_w + workers)) >=\
            (timespan/production_lines) * (workers/2) * (1 +  workers):
        workers += 1
    return workers

def element2dickt(root):
    ret_val = {}
    for el in root.findall("element"):
        key = el.find("key").text
        value = int(el.find("value").text)
        ret_val[key] = value

    return ret_val

def create_action(root):

    name = root.find("name")
    minerals = root.find("minerals")
    vespin = root.find( "vespin")
    workers = root.find( "workers")
    duration = root.find("duration")
    effects_e = root.find("effects")
    burrow_e = root.find("burrow")
    cost_e = root.find("cost")
    prereq_e = root.find("require")

    effects = element2dickt(effects_e)
    burrow = element2dickt(burrow_e)
    cost = element2dickt(cost_e)
    prereq = element2dickt(prereq_e)

    return TerranSearch.Action(name.text,int(workers.text),int(minerals.text),int(vespin.text), prereq,cost,burrow,int(duration.text),effects)

def get_Goals(filename):
    neco = filename+".xml"
    goal_tree = ET.parse(neco)
    ret_val = []
    root = goal_tree.getroot()
    race = root.attrib["race"]
    goals = root.findall("goal")

    for g in goals:
        name = g.find("name").text
        count = int(g.find("count").text)
        ret_val += [TerranSearch.Goal(name,count)]
    return race, ret_val

def getActionGraph(race):
    unit_tree = ET.parse("units_"+race+".xml")
    research_tree = ET.parse("research_" + race+".xml")
    buildings_tree = ET.parse("buildings_" + race+".xml")
    ret_val = jraph.JustificationGraph()#TerranSearch.ActionPool()
    u_root = unit_tree.getroot()
    b_root = buildings_tree.getroot()
    r_root = research_tree.getroot()
    u_actions = u_root.findall("action")
    b_actions = b_root.findall("action")
    r_actions = r_root.findall("action")
    for a in u_actions:
        action = create_action(a)
        ret_val.register_action(action)

    for a in b_actions:
        action = create_action(a)
        ret_val.register_action(action)
    for a in r_actions:
        action = create_action(a)
        ret_val.register_action(action)
    return ret_val

def export_plan(plan, outfile_name):
    f = open(outfile_name, "w")
    for action in plan:
        f.write(action.to_file() + "\n")
    f.close()


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

MINERAL_RATE = 0.05
VESPIN_RATE = 0.05
INNIT_WORKERS = 5
INNIT_MINERALS = 200
INNIT_VESPIN = 0
INNIT_STATE = {"Pop_Cap": 8, "Pop": 8,"Hatchery": 1, "Hatchery_Token": 1, "Base": 1, "Larva": 3}

start = time.time()
filename = sys.argv[1]
print(filename)
ofilname = sys.argv[1] + "_plan.out"

print("Starting up, boss!")
race,goals = get_Goals(filename)
graph = getActionGraph(race)


max_s,min_s,actions = graph.Filter(set(list(INNIT_STATE.keys())),goals)
pool = ActionPool()
minerals = 0
print(actions)
#to do action
for g in goals:
   minerals += pool.by_name[g.name].minerals
max_workers = MaximumWorkers(minerals,INNIT_WORKERS, MINERAL_RATE,pool.by_name[g.name].duration,
                            pool.by_name[g.name].minerals)
print("max workers = "+ str(max_workers))

in_state = TerranSearch.Status(INNIT_MINERALS,INNIT_VESPIN, INNIT_STATE,INNIT_WORKERS, MINERAL_RATE, VESPIN_RATE, max_workers)

pool.connect(in_state)
game = TerranSearch.Game(in_state, pool)
bestplan = TerranSearch.AstarSearch(game, pool, goals)
end = time.time()
#print(bestplan)
print(end-start)
#export_plan(bestplan,ofilname)

