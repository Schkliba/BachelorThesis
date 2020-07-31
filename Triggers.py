from actions import *



class Trigger:
    def __init__(self, resource, minimal_value, action: Action):
        self.resource = resource
        self.min = minimal_value
        self.reaction = action


class CostTrigger(Trigger):

    def __init__(self, resource, minimal_value, action: Action):
        super().__init__(resource, minimal_value, action)

    def validate(self, action) -> Action or None:
        if action.unary_cost[self.resource] >= self.min:
            return self.reaction
        else:
            return None


class EffectTrigger(Trigger):
    def __init__(self, resource, minimal_value, action: Action):
        super().__init__(resource, minimal_value, action)

    def validate(self, action) -> Action or None:
        if action.effect[self.resource] >= self.min:
            return self.reaction
        else:
            return None

class AbsoluteTrigger(Trigger):
    def __init__(self, resource, minimal_value, action: Action):
        super().__init__(resource, minimal_value, action)

    def validate(self, status) -> Action or None:
        if status.unaries[self.resource] >= self.min:
            return self.reaction
        else:
            return None
