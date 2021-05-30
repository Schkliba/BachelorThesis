import networkx as nx
import matplotlib.pyplot as plt
import random
import actions

class ActionGraph:
    def __init__(self):
        self.actions: [actions.Action] = []
        self.sequence = {}
        self.precondition = {}
        self.by_purpose: {str: actions.Action} = {}
        self.by_requirements: {str: actions.Action} = {}
        self.main_varibales = []
        self.G = nx.DiGraph()

    def register_action(self, action: actions.Action):
        self.sequence[action.name] = len(self.actions)
        self.actions.append(action)
        self.by_purpose[action.purpose] = action
        for p in action.preconditions():
            if p in self.by_requirements:
                self.by_requirements[p] += [action]
            else:
                self.by_requirements[p] = [action]
        if action.purpose not in self.main_varibales:
            self.main_varibales += [action.purpose]


    def plot_action_graph(self):
        for (i, a1) in enumerate(self.actions):
            for p in a1.preconditions():
                if p not in self.by_purpose:
                    continue
                a2 = self.by_purpose[p]
                self.G.add_edge(self.sequence[a2.name], self.sequence[a1.name])
        labels = {}
        for (i, a1) in enumerate(self.actions):
            labels[i] = a1.name

        pos = nx.spring_layout(self.G, k=1.5)
        options = {"node_size": 500, "alpha": 1}

        nx.draw_networkx_nodes(self.G, pos, nodelist=list(range(len(self.actions))), node_color="r", **options)
        nx.draw_networkx_edges(
            self.G,
            pos,
            edgelist=self.G.edges,
            width=2,
            alpha=0.5,
            edge_color="b",
        )

        nx.draw_networkx_labels(self.G, pos, labels, font_size=12)
        #nx.draw_planar(self.G, with_labels = True)
        plt.show()

if __name__ == '__main__':

    # Create a directed graph
    G = nx.path_graph(8)
    # Randomize edge weights
    nx.set_edge_attributes(G, {e: {'weight': random.randint(1, 9)} for e in G.edges})

    nx.draw(G)
    plt.show()