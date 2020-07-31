class Goals:
    def __init__(self, goals):
        self.goals = goals

    def find_shortest_path_from(self,state,actions):
            ret_plan = []
            depth = 0
            path_lenght = 0
            for g in self.goals:
                if state.check(g):
                    continue
                goal_plan = []


                for a in actions:
                    #if a.contradicts(goals):
                   #     print("Kontradikce: " + str(feasible_actions[index]))
                    #    print("Akce kontradikuje některý goal, nelze použít")
                     #   continue
                    #     if feasible_actions[index].reached(in_state):
                    #          continue
                    new_goals = a.preconditions()
                    new_state = dict(in_state)
                    new_state = feasible_actions[index].apply_on(new_state)
                    print("Selecting Action: " + str(feasible_actions[index]))
                    print("NewGoals: " + str(new_goals))

                    cur_plan = Simplesearch(new_state, new_goals, realm, plan + [feasible_actions[index]], depth + 1)

                    if len(cur_plan) == 0: continue
                    if len(goal_plan) > 0 and len(goal_plan) > len(cur_plan):
                        goal_plan = cur_plan
                    elif len(goal_plan) == 0:
                        goal_plan = cur_plan

                ret_plan = goal_plan

            return ret_plan