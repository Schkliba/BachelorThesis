import sys
import time
import xml.etree.ElementTree as ET
import TerranSearchv3 as TerranSearch

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

def get_Goals(tree):
    ret_val = []
    goals = tree.findall("goal")
    for g in goals:
        name = g.find("name").text
        count = int(g.find("count").text)
        ret_val += [TerranSearch.Goal(name,count)]
    return ret_val

def get_ActionPool(tree):

    ret_val = TerranSearch.ActionPool()
    root = tree.getroot()
    actions = root.findall("action")
    for a in actions:
        action = create_action(a)
        ret_val.register_action(action)

    return ret_val

def export_plan(plan, outfile_name):
    f = open(outfile_name, "w")
    for action in plan:
        f.write(action.to_file() + "\n")
    f.close()

MINERAL_RATE = 0.05
VESPIN_RATE = 0.05
INNIT_WORKERS = 5
INNIT_MINERALS = 300
INNIT_VESPIN = 0

start = time.time()
filename = sys.argv[1]
ofilname = sys.argv[1] + "_plan.out"
tree = ET.parse(filename)
print("Starting up, boss!")
race = tree.getroot().attrib["race"]
pool = get_ActionPool(tree)
goals = get_Goals(tree)
minerals = 0
for g in goals:
    minerals += pool.by_name[g.name].minerals
max_workers = MaximumWorkers(minerals,INNIT_WORKERS, MINERAL_RATE,pool.by_name[g.name].duration,
                             pool.by_name[g.name].minerals)
print("max workers = "+ str(max_workers))
in_state = TerranSearch.Status(INNIT_MINERALS,INNIT_VESPIN,{"Base":1},INNIT_WORKERS, MINERAL_RATE, VESPIN_RATE, max_workers)

pool.connect(in_state)
game = TerranSearch.Game(in_state, pool)
bestplan = TerranSearch.AstarSearch(game, pool, goals)
end = time.time()
print(bestplan)
print(end-start)
export_plan(bestplan,ofilname)

