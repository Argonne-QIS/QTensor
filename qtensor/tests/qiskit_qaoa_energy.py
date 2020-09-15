import qiskit
import numpy as np
import networkx as nx
from functools import partial
from qiskit.optimization.ising.max_cut import get_operator as get_maxcut_operator
from qiskit.aqua.algorithms.adaptive.qaoa.var_form import QAOAVarForm
# Use these lines for import with new qiskit(>=0.19). The resulting QAOA energy will be wrong
# The change is somewhere in this file: https://github.com/Qiskit/qiskit-aqua/blob/0.7.5/qiskit/aqua/algorithms/minimum_eigen_solvers/qaoa/var_form.py
# It's ridiculous that nobody found this and never fixed, August 2020


# from qiskit.optimization.applications.ising.max_cut import get_operator as get_maxcut_operator
# from qiskit.aqua.algorithms.minimum_eigen_solvers.qaoa.var_form import QAOAVarForm
from qiskit import Aer, execute
from qiskit.compiler import transpile

def state_num2str(basis_state_as_num, nqubits):
    return '{0:b}'.format(basis_state_as_num).zfill(nqubits)

def state_str2num(basis_state_as_str):
    return int(basis_state_as_str, 2)

def state_reverse(basis_state_as_num, nqubits):
    basis_state_as_str = state_num2str(basis_state_as_num, nqubits)
    new_str = basis_state_as_str[::-1]
    return state_str2num(new_str)

def get_adjusted_state(state):
    nqubits = np.log2(state.shape[0])
    if nqubits % 1:
        raise ValueError("Input vector is not a valid statevector for qubits.")
    nqubits = int(nqubits)

    adjusted_state = np.zeros(2**nqubits, dtype=complex)
    for basis_state in range(2**nqubits):
         adjusted_state[state_reverse(basis_state, nqubits)] = state[basis_state]
    return adjusted_state


def state_to_ampl_counts(vec, eps=1e-15):
    """Converts a statevector to a dictionary
    of bitstrings and corresponding amplitudes
    """
    qubit_dims = np.log2(vec.shape[0])
    if qubit_dims % 1:
        raise ValueError("Input vector is not a valid statevector for qubits.")
    qubit_dims = int(qubit_dims)
    counts = {}
    str_format = '0{}b'.format(qubit_dims)
    for kk in range(vec.shape[0]):
        val = vec[kk]
        if val.real**2+val.imag**2 > eps:
            counts[format(kk, str_format)] = val
    return counts


def obj_from_statevector(sv, obj_f, precomputed=None):
    """Compute objective from Qiskit statevector
    For large number of qubits, this is slow. 
    To speed up for larger qubits, pass a vector of precomputed energies
    for QAOA, precomputed should be the same as the diagonal of the cost Hamiltonian
    """
    if precomputed is None:
        adj_sv = get_adjusted_state(sv)
        counts = state_to_ampl_counts(adj_sv)
        assert(np.isclose(sum(np.abs(v)**2 for v in counts.values()), 1))
        return sum(obj_f(np.array([int(x) for x in k])) * (np.abs(v)**2) for k, v in counts.items())
    else:
        return np.dot(precomputed, np.abs(sv)**2)

def maxcut_obj(x,w):
    """Compute -1 times the value of a cut.
    Args:
        x (numpy.ndarray): binary string as numpy array.
        w (numpy.ndarray): adjacency matrix.
    Returns:
        float: value of the cut.
    """
    X = np.outer(x, (1 - x))
    return -np.sum(w * X)

def simulate_qiskit_amps(G, gamma, beta):
    assert len(gamma) == len(beta)
    p = len(gamma)

    w = nx.adjacency_matrix(G, nodelist=list(G.nodes())).toarray()
    obj = partial(maxcut_obj,w=w)
    C, _ = get_maxcut_operator(w)
    parameters = np.concatenate([beta, -np.array(gamma)])

    # When transitioning to newer qiskit this raises error.
    # Adding C.to_opflow() removes the error, but the values are still wrong
    varform = QAOAVarForm(p=p,cost_operator=C)
    circuit = varform.construct_circuit(parameters)

    circuit_qiskit = transpile(circuit, optimization_level=0,basis_gates=['u1', 'u2', 'u3', 'cx'])
    #print(circuit_qiskit)
    sv = execute(circuit, backend=Aer.get_backend("statevector_simulator")).result().get_statevector()

    res = - obj_from_statevector(sv, obj)
    return res

def test_simulate_qiskit_amps():
    elist = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [0, 5], [1, 6], [2, 7], [3, 8], [4, 9], [5, 7], [5, 8], [6, 8], [6, 9], [7, 9]]
    G = nx.OrderedGraph()
    G.add_edges_from(elist)
    parameters = np.array([5.192253984583296, 5.144373231492732, 5.9438949617723775, 5.807748946652058, 3.533458907810596, 6.006206583282401, 6.122313961527631, 6.218468942101044, 6.227704753217614, 

0.3895570099244132, -0.1809282325810937, 0.8844522327007089, 0.7916086532373585, 0.21294534589417236, 0.4328896243354414, 0.8327451563500539, 0.7694639329585451, 0.4727893829336214])
    beta = parameters[:9]
    gamma = -parameters[9:]

    result = simulate_qiskit_amps(G, gamma, beta)
    print(result)
    assert abs(abs(result) - 12) < 1e-2

if __name__ == "__main__":
    test_simulate_qiskit_amps()

