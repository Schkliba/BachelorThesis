class Action:

    def __init__(self,name: str,minerals,gas,prereq,cost,burrow,duration,id = 0,effect=None,ef_time_map=None):
        self.name = name
        self.id = id
        self.minerals = minerals
        self.vespin = gas


        self.prereq = prereq#před
        self.unary_cost = cost #zničené suroviny
        self.burrow = burrow #propujčené suroviny
        self.duration = duration
        if effect is None: self.effect = {}
        else: self.effect = effect #po
        if ef_time_map is None:
            self.ef_time_map = {}
        else:
            self.ef_time_map = ef_time_map  # po
        self.precondit = {}

        for u in burrow:
           self.precondit[u] = burrow[u]
        for u in cost:
            if u not in self.precondit:
                self.precondit[u] = cost[u]
            else:
                self.precondit[u] += cost[u]
        for u in self.prereq:
            if u not in self.precondit:
                self.precondit[u] = prereq[u]
            else:
                self.precondit[u] += prereq[u]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.name + "("+str(self.duration)+")"


    def schedule(self,from_t):
        mapa = {}
        for m in self.ef_time_map:
            mapa[m] = {}
            for i in self.ef_time_map[m]:
                mapa[m][i+from_t]= self.ef_time_map[m][i]

        return ScheduledAction(self.name, self.minerals,self.vespin,self.prereq,self.unary_cost,
                               self.burrow,self.duration,self.effect,mapa,from_t)

    def preconditions_dict(self):
        return self.precondit

    def preconditions(self):
        return list(self.precondit.keys())

    def postconditions(self):
        return list(self.effect.keys())

    def register_effect(self,name ,number, time:int):
        if name in self.ef_time_map:
            self.effect[name] += number
        else:
            self.effect[name] = number

        if name in self.ef_time_map:
            self.ef_time_map[name][time] = number
        else:
            self.ef_time_map[name] = {}
            self.ef_time_map[name][time] = number

    def get_effect(self, e):
        if e in self.ef_time_map:
            return self.effect[e]
        else:
            return self.effect[e]
class ScheduledAction(Action):

    def __init__(self,name,  minerals, gas, prereq, cost, burrow, duration, effect, ef_map, start_time):
        super().__init__(name,  minerals, gas, prereq, cost, burrow, duration, 0,effect, ef_map)
        self.start_time = start_time
        self.end_time = start_time+duration
        self.surplus_time = 0
        self.finished = False

    def add_time(self, time):
        self.surplus_time = time
        self.start_time += time
        new_map = {}
        for m in self.ef_time_map:
            new_map[m]={}
            for i in self.ef_time_map[m]:
                temp = self.ef_time_map[m][i]
                new_map[m][i+time] = temp
        self.ef_time_map = new_map
        self.end_time += time

    def get_effect(self, e):
        if e in self.ef_time_map:
            return self.effect[e], self.ef_time_map[e]
        else:
            return self.effect[e], self.end_time

    def __eq__(self, other):
        return (self.name == other.name) and (self.start_time == other.start_time) and (self.duration == other.duration) and (self.finished == other.finished)

    def __str__(self):
        return str(self.name) +"("+str(self.start_time)+";"+str(self.end_time)+")"

    def __repr__(self):
        return self.__str__()

    def to_file(self):
        return str(self.name) +";"+str(self.start_time)+";"+str(self.end_time)+";"+str(self.minerals)+";"+str(self.vespin)

class ActionPool:
    def __init__(self):
        self.connected = False
        self.ref_state = None
        self.actions = []
        self.plannable = []
        self.idle_action = None
        self.unplannable = []
        self.by_name = {}

    def __repr__(self):
        out = "["
        for a in self:
            out+=str(a)
        out+="]"
        return out

    def __len__(self):
        return len(self.plannable)

    def __str__(self):
        return self.__repr__()

    def __iter__(self):
        return self.plannable.__iter__()

    def max_duration(self):
        if len(self.actions) < 1: return 0
        max_duration = self.actions[0].duration
        for a in self.actions:
            if a.duration > max_duration:
                max_duration = a.duration

        return max_duration

    def min_duration(self):
        if len(self.actions)< 1: return 0
        min_duration = self.actions[0].duration
        for a in self.actions:
            if a.duration <  min_duration:
                min_duration = a.duration

        return min_duration

    def register_action(self, action):
        print("Registering action:"+str(action))
        self.actions += [action]
        for eff in list(action.effect.keys()):
            self.by_name[eff] = action

    def connect(self, state):
        self.ref_state = state
        self.plannable = []
        for a in self.actions:
            if state.is_plannable(a):
                self.plannable += [a]


    def refresh(self):
        self.plannable= []
        for a in self.actions:
            if self.ref_state.is_plannable(a):
                self.plannable += [a]

