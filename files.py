import xml.etree.ElementTree as ET


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
    vespin = root.find("vespin")
    purpose = root.find("purpose")
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
    act.purpose = purpose.text
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
    unit_tree = ET.parse("./Data/units_"+race+".xml")
    research_tree = ET.parse("./Data/research_" + race+".xml")
    buildings_tree = ET.parse("./Data/buildings_" + race+".xml")

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


