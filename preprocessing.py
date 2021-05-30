import copy
import actions


class FilterRequire:
    order = {'r': 1, 'c': 2, 'b': 3}

    def __init__(self):
        self.actions = []
        self.precondition = {}
        self.by_purpose = {}
        self.main_variables = {}

    def register_action(self, action):
        self.actions.append(action)
        self.by_purpose[action.purpose] = action
        self.main_variables[action.purpose] = None;

    def recursion(self, status, goals, main_variables):
        sub_variables = {}
        print("Goals:" + str(goals))
        print("State:" + str(status))
        if self.covers(status, goals):
            print('It covers')
            return main_variables
        for a in self.actions:
            if self.solves_some(a, goals):
                print('Solves!')
                new_state, new_goals, new_variables = self.apply(a, status,goals, main_variables)
                branch_ac = self.recursion(new_state, new_goals, new_variables)
                sub_variables = self.merge(sub_variables, branch_ac)

        return sub_variables

    def solves_some(self, action:actions.Action, goals):
        for e in action.effects():
            if e in goals:
                return True
        return False

    def apply(self, action: actions.Action, current_state, current_goals, main_variables):
        new_goals = copy.copy(current_goals)
        new_variables = copy.copy(main_variables)
        new_state = copy.copy(current_state)
        pre = action.preconditions()
        post = action.effects()
        for g in pre:
            if g not in current_state: new_goals[g] = 1
        for g in post:
            if g in new_goals:
                del new_goals[g]
            new_state[g] = 1
        for r in action.prereq:
            new_variables[r] = 'r'
        for r in action.unary_cost:
            new_variables[r] = 'c'
        for r in action.burrow:
            new_variables[r] = 'b'

        return new_state,new_goals, new_variables

    def covers(self,status, goals):
        for g in goals:
            if g not in status:
                return False
        return True

    def merge(self, variables1, variables2):
        new_vars = {}
        for i in variables1:
            new_vars[i] = variables1[i]
        for i in variables2:
            if i in new_vars:
                if self.order[variables2[i]] > self.order[new_vars[i]]:
                    new_vars[i] = variables2[i]
            else:
                new_vars[i] = variables2[i]

        return new_vars
