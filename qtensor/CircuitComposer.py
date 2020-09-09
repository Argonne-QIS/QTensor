from loguru import logger as log
from qtensor.utils import get_edge_subgraph
import networkx as nx
from .OpFactory import CircuitCreator

class CircuitComposer(CircuitCreator):
    def __init__(self, *args, **params):
        super().__init__(*args, **params)
        self.params = params

    def layer_of_Hadamards(self):
        for q in self.qubits:
            self.apply_gate(self.operators.H, q)

    def create(self):
        raise NotImplementedError


class QAOAComposer(CircuitComposer):
    def __init__(self, graph, *args, **kwargs):
        n_qubits = graph.number_of_nodes()
        super().__init__(n_qubits, *args, **kwargs)

        self.graph = graph

    def x_term(self, u, beta):
        #self.circuit.append(self.operators.H(u))
        self.apply_gate(self.operators.XPhase, u, alpha=2*beta)
        #self.circuit.append(self.operators.H(u))
    def mixer_operator(self, beta):
        G = self.graph
        for n in G:
            qubit = self.qubits[n]
            self.x_term(qubit, beta)

    def append_zz_term(self, q1, q2, gamma):
        try:
            self.apply_gate(self.operators.CC, q1, q2, alpha=2*gamma)
        except AttributeError:
            pass
        self.apply_gate(self.operators.cX, q1, q2)
        self.apply_gate(self.operators.ZPhase, q2, alpha=2*gamma)
        self.apply_gate(self.operators.cX, q1, q2)
    def cost_operator_circuit(self, gamma):
        for i, j in self.graph.edges():
            u, v = self.qubits[i], self.qubits[j]
            self.append_zz_term(u, v, gamma)


    def ansatz_state(self):
        beta, gamma = self.params['beta'], self.params['gamma']

        assert(len(beta) == len(gamma))
        p = len(beta) # infering number of QAOA steps from the parameters passed
        self.layer_of_Hadamards()
        # second, apply p alternating operators
        for i in range(p):
            self.cost_operator_circuit(gamma[i])
            self.mixer_operator(beta[i])
        return self.circuit

    def energy_edge(self, i, j):
        #self.circuit.append(self.operators.CC(u, v))
        u, v = self.qubits[i], self.qubits[j]
        self.apply_gate(self.operators.Z, u)
        self.apply_gate(self.operators.Z, v)

