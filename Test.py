import sys
import time
import TerranTest as TerranSearch
import hmaxer
import decimal
import preprocessing
import json
decimal.getcontext().prec = 28 #počet decimálních míst na které se implicině zaokrouhluje

import justifilter as jraph
import files

def MaximumWorkers(volume, innit_w, rate, cost, timespan, production_lines = 1):
    workers = 0
    while ((volume/rate)/(innit_w + workers))+((cost/rate)/(innit_w + workers)) >=\
            (timespan/production_lines) * (workers/2) * (1 +  workers):
        workers += 1
    return workers

def triggers():
    trigger_tree = ET.parse("units_" + race + ".xml")

MINERAL_RATE = 0.05
VESPIN_RATE = 0.05
INNIT_WORKERS = 5
INNIT_MINERALS = 200
INNIT_VESPIN = 200
an_state = {'Larva', 'Lair_Token', 'Larva_Slot', 'Hive', 'Spawning_Pool', 'Pop_Cap', 'Base', 'Worker', 'Hydralisk', 'Ultralisk', 'Hatchery_Token', 'Hydralisk_Den', 'Ultralisk_Cavern', 'Larva_Timer', 'Vespin', 'Queens_Nest', 'Nexus'}
ne_state = {'Pop_Cap': 10, 'Hatchery_Token': 1, 'Nexus': 1, 'Base': 1, 'Larva_Timer': 1, 'Vespin': 1, 'Larva_Slot': 1, 'Spawning_Pool': 3, 'Lair_Token': 1, 'Hydralisk_Den': 1, 'Hydralisk': 2, 'Queens_Nest': 1, 'Hive': 1,'Zergling_Cavern': 1, 'Ultralisk_Cavern': 1, 'Ultralisk': 1}
INNIT_STATE = {"Pop_Cap": 8, "Pop": 8,"Hatchery": 1, "Hatchery_Token": 1, "Nexus":1, "Base": 1, "Larva_Timer":1, "Larva": 3, "Worker": 5, "Vespin": 1}
simp_state = {'Pop_Cap', 'Hatchery_Token', 'Nexus', 'Base', 'Larva_Timer', 'Vespin', " Hydralisk",'Larva_Slot', 'Spawning_Pool', 'Lair_Token', 'Hydralisk_Den', 'Queens_Nest', 'Hive','Zergling', 'Ultralisk_Cavern'}
newsimp = {'Larva', 'Nexus', 'Zergling', 'Vespin', 'Queens_Nest', 'Spawning_Pool', 'Lair_Token', 'Hydralisk_Den', 'Hive', 'Hatchery_Token', 'Base', 'Pop_Cap', 'Larva_Timer', 'Larva_Slot', 'Worker'}
newersimp={'Larva_Slot', 'Ultralisk_Cavern', 'Lair_Token', 'Base', 'Hive', 'Hatchery_Token', 'Larva_Timer', 'Pop_Cap', 'Larva', 'Queens_Nest', 'Spawning_Pool', 'Zergling', 'Hydralisk_Den', 'Nexus', 'Vespin'}
test1 = {'Larva', 'Hydralisk_Den', 'Ultralisk_Cavern', 'Hatchery_Token', 'Nexus', 'Vespin', 'Zergling', 'Lair_Token', 'Base', 'Queens_Nest', 'Pop_Cap', 'Hive', 'Larva_Timer', 'Hydralisk', 'Spawning_Pool'}
#{'Pop_Cap': 10, 'Hatchery_Token': 1, 'Base': 1, 'Larva_Timer': 1, 'Larva': 2, 'Worker': 3, 'Vespin': 1, 'Larva_Slot': 1, 'Spawning_Pool': 1, 'Lair_Token': 1, 'Spire': 1, 'Mutalisk': 2, 'Queens_Nest': 1, 'Hive': 1, 'Ultralisk_Cavern': 1, 'Ultralisk': 1}
    #{'Pop_Cap': 9, 'Pop': 1, 'Hatchery_Token': 1, 'Base': 1, 'Larva_Timer': 1, 'Worker': 5, 'Vespin': 1, 'Larva_Slot': 3, 'Spawning_Pool': 1, 'Lair_Token': 1, 'Lair': 1, 'Spire': 1, 'Mutalisk': 3}

start = time.time()
filename = sys.argv[1]


print("Starting up, boss!")
race,goals,goals2 = files.get_Goals(filename)
graph = files.getActionGraph(race)

json_file = open("./Data/" + race + ".json")
max_mask = json.load(json_file)
json_file.close()

print(actions)

def add(a,b):
    return a+b

#smth = hmaxer.CumulativeHeuristic(max)
#wow = hmaxer.ParallelHeuristic(max)
#llb = hmaxer.LLBHeuristic(max,min)
prep = preprocessing.FilterRequire()
for a in actions:
    #wow.register_action(a)
    #llb.register_action(a)
    #smth.register_action(a)
    prep.register_action(a)
variable_use = prep.recursion(INNIT_STATE,goals2, {})

for v in variable_use:
    if variable_use[v] == 'r':
        max_mask[v] = 1

#max_s,actions = graph.Filter(INNIT_STATE,goals)




goals_s = set()
#minerals = 0
#for g in goals:
#   minerals += pool.by_name[g.name].minerals
#   goals_s.add(g.name)
#max_workers = MaximumWorkers(minerals,INNIT_WORKERS, MINERAL_RATE,pool.by_name[g.name].duration,
 #                           pool.by_name[g.name].minerals)
#print("max workers = "+ str(max_workers))

#in_state = TerranSearch.Status(INNIT_MINERALS,INNIT_VESPIN, INNIT_STATE,INNIT_WORKERS, MINERAL_RATE, VESPIN_RATE, max_workers)
#print(hmaxer.h(INNIT_STATE,goals2))
#llb.take_measures()
#wow.take_measures()
#smth.take_measures()
print("***********************************************************")
#goals2 = {'Ultralisk': 2, 'Hydralisk': 2}
#print(goals2)
#print(simp_state)
#k = (llb.LM_Cutting(test1,goals2))
#z = (wow.h(test1,goals2))
#print(k)
#print(z)
print(max_mask)
#print(smth.h(ne_state,goals2))
#print(smth.h(ne_state,goals2,lambda x: x.vespin))
end = time.time()
print(end-start)
#export_plan(bestplan,ofilname)

