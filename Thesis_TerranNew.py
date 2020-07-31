
def betterplan(planA, planB):
    print("A:"+str(planA.time)+" B:"+str(planB.time))
    return planA.time <= planB.time

def AstarSearch(state: GameState, actions: ActionPool, goals:List[Goal]):
    step = actions.max_duration()
    min = actions.min_duration()
    base = 0
    for g in goals:
        base += g.count*step
    ub_time = 1 + base


    plan_distance=0
    for g in goals:
        progress = state.check(g)
        if progress <= 0:
            goals.remove(g)
        plan_distance += progress

    bestplan = MockPlan(0,plan_distance)
    planner = PanningWindow()
    while type(bestplan) == MockPlan:
        print(state)
        bestplan = AStarDFS(state, actions, planner, goals, 0, ub_time)
        ub_time += base
    return bestplan


def AStarDFS(state: GameState,action_pool: ActionPool, planner:PlanningWindow, goals, current_time, ub_time):

    print(current_time)
    besttime=ub_time



    goal_distance = state.check_all(goals) #distance of every childnode  <= goal_distance
    best_distance = goal_distance
    bestplan = MockPlan(ub_time, best_distance)
    if goal_distance <= 0:
        print("Vyhráli jsme!")
        return planner.get_plan(goal_distance)

    potential = planner.potential_end()
    if potential >= ub_time:
        print("Limitní čas...")
        return MockPlan(potential,goal_distance)#něco co není potenciál




    #planovatelné akce od tohoto okamžiku
    print(action_pool)



    for a in action_pool:

        # finished
        if not state.is_plannable(a): continue

        new_current_time,sch_a = state.plan_finished_action(a)
        planner.plan(sch_a)
        finished_actions = planner.refresh_to(current_time)
        state.finish_actions(finished_actions)
        print("Dem dovnitř! f")
        plan = AStarDFS(state, action_pool, planner,goals, new_current_time, besttime)
        if besttime > plan.time:
            print("Changing best plan" + str(besttime) + str(bestplan) + "/" + str(plan))
            bestplan = plan
            besttime = plan.time
        print(state.unaries)
        print("Dem ven! f- " + str(current_time))
        #game.unplan_last()
        unused_actions = planner.reverse(current_time)
        state.reverse(unused_actions)
        print(state.unaries)
        surplus = state.project(a.minerals,a.vespin)
        was_in_range = False
        # kontroluje jestli existuje taková akce, aby se dala naplánovat souběžně s touto akcí.
        for b in action_pool:
            if not state.is_plannable(a): continue
            # cena b < (stav po zaplacení a) + (minerály získáné po dobu trvání a)
            if (b.minerals < (state.minerals - a.minerals) + state.wait_minerals(a.duration+surplus ,state.unaries["Worker"]) and
                b.vespin < (state.vespin - a.vespin) + state.wait_vespin(a.duration + surplus,
                                                                                           state.unaries["Worker"])):
                was_in_range = True
        if was_in_range:
        #unfinished
            new_current_time, sch_a = state.plan_next_action(a)
            planner.plan(sch_a)
            finished_actions = planner.refresh_to(current_time)
            state.finish_actions(finished_actions)
            print("Dem dovnitř!")
            plan = AStarDFS(state, action_pool, planner,goals, new_current_time, besttime)
            if besttime > plan.time :
                print("Changing best plan"+"-"+str(besttime)+str(bestplan)+"/"+str(plan))
                bestplan = plan
                besttime = plan.time
            print(state.unaries)
            print("Dem ven! - "+str(current_time))


            unused_actions = planner.reverse(current_time)
            state.reverse(unused_actions)
            print(state.unaries)

    return bestplan