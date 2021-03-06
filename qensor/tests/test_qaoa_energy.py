from qensor import CirqQAOAComposer, QtreeQAOAComposer
from qensor import QAOAQtreeSimulator
from qensor.Simulate import CirqSimulator, QtreeSimulator
from qensor.FeynmanSimulator import FeynmanSimulator
from qensor.optimisation.Optimizer import TamakiTrimSlicing, TreeTrimSplitter
from qensor.tests.qiskit_qaoa_energy import simulate_qiskit_amps 
import numpy as np
import networkx as nx

def get_test_problem(n=14, p=2, d=3):
    w = np.array([[0,1,1,0],[1,0,1,1],[1,1,0,1],[0,1,1,0]])
    G = nx.from_numpy_matrix(w)

    G = nx.random_regular_graph(d, n)
    gamma, beta = [np.pi/3]*p, [np.pi/2]*p
    return G, gamma, beta

def test_qaoa_energy_vs_qiskit():
    G, gamma, beta = get_test_problem()
    sim = QAOAQtreeSimulator(QtreeQAOAComposer)
    E = sim.energy_expectation(
        G, gamma=gamma, beta=beta)

    assert E

    gamma, beta = -np.array(gamma)*2*np.pi, np.array(beta)*np.pi
    qiskit_E = simulate_qiskit_amps(G, gamma, beta)
    assert np.isclose(E, qiskit_E)

def test_qaoa_energy_multithread():
    G, gamma, beta = get_test_problem()
    sim = QAOAQtreeSimulator(QtreeQAOAComposer)
    res = sim.energy_expectation_parallel(
        G, gamma=gamma, beta=beta,
        n_processes=4
    )
    print('result', res)
    assert res
    res_1 = sim.energy_expectation(
        G, gamma=gamma, beta=beta)
    print('result', res_1)
    assert res_1 - res < 1e-6

class FeynmanQAOASimulator(QAOAQtreeSimulator, FeynmanSimulator):
    pass

def test_qaoa_energy_feynman():
    G, gamma, beta = get_test_problem(14, 3, 3)
    sim = QAOAQtreeSimulator(QtreeQAOAComposer)
    res = sim.energy_expectation(
        G, gamma=gamma, beta=beta)
    print('result', res)

    sim = FeynmanQAOASimulator(QtreeQAOAComposer)
    sim.opt_args['tw_bias'] = 6
    sim.optimizer = TreeTrimSplitter
    res_1 = sim.energy_expectation(
        G, gamma=gamma, beta=beta)
    print('result', res_1)
    assert np.isclose(res, res_1)

if __name__ == '__main__':
    test_qaoa_energy_multithread()
