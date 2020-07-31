import sys
import time
import xml.etree.ElementTree as ET
import TerranTest as TerranSearch
import hmaxer
import decimal
decimal.getcontext().prec = 28 #počet decimálních míst na které se implicině zaokrouhluje

import justifilter as jraph

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

def timed_element2dickt(root):
    time_map = {}
    ret_val = {}
    for el in root.findall("element"):

        key = el.find("key").text
        value = int(el.find("value").text)
        if "time" in el.attrib:
            time_map[key] = int(el.attrib["time"])
        ret_val[key] = value

    return ret_val,time_map
ACTION_COUNTER = 1

def create_action(root):

    global ACTION_COUNTER
    name = root.find("name")
    minerals = root.find("minerals")
    vespin = root.find( "vespin")
    duration = root.find("duration")
    effects_e = root.find("effects")
    burrow_e = root.find("burrow")
    cost_e = root.find("cost")
    prereq_e = root.find("require")

    #effects,time_map = timed_element2dickt(effects_e)
    burrow = element2dickt(burrow_e)
    cost = element2dickt(cost_e)
    prereq = element2dickt(prereq_e)

    act = TerranSearch.Action(name.text,int(minerals.text),int(vespin.text), prereq,cost,burrow,int(duration.text), ACTION_COUNTER)
    ACTION_COUNTER += 1
    for el in effects_e.findall("element"):
        key = el.find("key").text
        value = int(el.find("value").text)
        if "time" in el.attrib:
            time = int(el.attrib["time"])
            act.register_effect(key,value,time)
        else:
            act.register_effect(key,value,act.duration)
    return act

def get_Goals(filename):
    neco = filename+".xml"
    goal_tree = ET.parse(neco)
    ret_val = []
    ret_val2 = {}
    root = goal_tree.getroot()
    race = root.attrib["race"]
    goals = root.findall("goal")

    for g in goals:
        name = g.find("name").text
        count = int(g.find("count").text)
        ret_val += [TerranSearch.Goal(name, count)]
        ret_val2[name] = count
    return race, ret_val, ret_val2

def getActionGraph(race):
    unit_tree = ET.parse("units_"+race+".xml")
    research_tree = ET.parse("research_" + race+".xml")
    buildings_tree = ET.parse("buildings_" + race+".xml")
    ret_val = jraph.JustificationGraph()#TerranSearch.ActionPool()
    #ret_val2 = LLB.JustificationGraph()
    u_root = unit_tree.getroot()
    b_root = buildings_tree.getroot()
    r_root = research_tree.getroot()
    u_actions = u_root.findall("action")
    b_actions = b_root.findall("action")
    r_actions = r_root.findall("action")
    for a in u_actions:
        action = create_action(a)
        ret_val.register_action(action)
        #ret_val2.register_action(action)
    for a in b_actions:
        action = create_action(a)
        ret_val.register_action(action)
        #ret_val2.register_action(action)
    for a in r_actions:
        action = create_action(a)
        ret_val.register_action(action)
        #ret_val2.register_action(action)
    return ret_val

def export_plan(plan, outfile_name):
    f = open(outfile_name, "w")
    for action in plan:
        f.write(action.to_file() + "\n")
    f.close()

def triggers():
    trigger_tree = ET.parse("units_" + race + ".xml")

MINERAL_RATE = 0.05
VESPIN_RATE = 0.05
INNIT_WORKERS = 5
INNIT_MINERALS = 200
INNIT_VESPIN = 200
ne_state={'Pop_Cap': 10, 'Hatchery_Token': 1, 'Base': 1, 'Larva_Timer': 1, 'Larva': 2, 'Worker': 3, 'Vespin': 1, 'Larva_Slot': 1, 'Spawning_Pool': 1, 'Lair_Token': 1, 'Spire': 1, 'Mutalisk': 2, 'Queens_Nest': 1, 'Hive': 1, 'Ultralisk_Cavern': 1, 'Ultralisk': 1}
INNIT_STATE = {"Pop_Cap": 8, "Pop": 8,"Hatchery": 1, "Hatchery_Token": 1, "Base": 1, "Larva_Timer":1, "Larva": 3, "Worker": 5}
    #{'Pop_Cap': 10, 'Hatchery_Token': 1, 'Base': 1, 'Larva_Timer': 1, 'Larva': 2, 'Worker': 3, 'Vespin': 1, 'Larva_Slot': 1, 'Spawning_Pool': 1, 'Lair_Token': 1, 'Spire': 1, 'Mutalisk': 2, 'Queens_Nest': 1, 'Hive': 1, 'Ultralisk_Cavern': 1, 'Ultralisk': 1}
    #{'Pop_Cap': 9, 'Pop': 1, 'Hatchery_Token': 1, 'Base': 1, 'Larva_Timer': 1, 'Worker': 5, 'Vespin': 1, 'Larva_Slot': 3, 'Spawning_Pool': 1, 'Lair_Token': 1, 'Lair': 1, 'Spire': 1, 'Mutalisk': 3}

#INNIT_STATE = {"Worker":1}

start = time.time()
filename = "Zerg_Mocker"


print("Starting up, boss!")
race,goals,goals2 = get_Goals(filename)
graph = getActionGraph(race)

max_s,actions = graph.Filter(INNIT_STATE,goals)

print(max_s)

print(actions)

def add(a,b):
    return a+b

hmaxer = hmaxer.CumulativeHeuristic(max)
for a in actions:
    hmaxer.register_action(a)




minerals = 0



goals_s = set()
#for g in goals:
#   minerals += pool.by_name[g.name].minerals
#   goals_s.add(g.name)
#max_workers = MaximumWorkers(minerals,INNIT_WORKERS, MINERAL_RATE,pool.by_name[g.name].duration,
 #                           pool.by_name[g.name].minerals)
#print("max workers = "+ str(max_workers))

#in_state = TerranSearch.Status(INNIT_MINERALS,INNIT_VESPIN, INNIT_STATE,INNIT_WORKERS, MINERAL_RATE, VESPIN_RATE, max_workers)
print(hmaxer.h(INNIT_STATE,goals2))


end = time.time()
print(end-start)
#export_plan(bestplan,ofilname)

