from types import DynamicClassAttribute
from numpy.core.fromnumeric import shape, size
import pyrofiler
from typing import List
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from functools import lru_cache
import itertools
import platform
import importlib
import os, psutil

from base import LasyModule, BenchResult, Backend, get_gpu_props_json, Benchmark, Numpy, TorchCuda, Cupy, CuTensor

np = LasyModule('numpy')

import sys
import os
sys.path.append(os.environ['HOME']+"/.local")
exatn = LasyModule('exatn')

class TncontractBench(Benchmark):    
    @staticmethod
    def get_task_type():
        return "tncontract"
    
    @classmethod
    def get_params(cls, *sizes):
        ops = np.prod(sizes[0]) * sizes[1][3] 
        param_in = np.prod(sizes[0]) + np.prod(sizes[1])
        param_out = sizes[0][0] * sizes[0][2] * sizes[1][3]
        return ops.item(), param_in.item(), param_out

    @classmethod
    def benchmark(cls, backend:Backend, num_tensors, *sizes, dtype='float', **args):
        num_tensors, *sizes = backend.get_ready(num_tensors, *sizes)
        operation = backend.get_tncontract()
        with cls.timing(callback=lambda x: None) as gen:
            tensors = backend.gen_tensors(num_tensors, *sizes, dtype=dtype)
        with cls.timing(callback=lambda x: None) as prep:
            for i in range(len(tensors)):
                tensors[i] = backend.prepare(tensors[i])
        with cls.timing(callback=lambda x: None) as op:
            if 'contraction' in args:
                out_tensor = operation(args['contraction'], *tensors)
            else:
                out_tensor = operation(*tensors)
        with cls.timing(callback=lambda x: None) as get:
            zr = backend.get_result(out_tensor)
        return zr, BenchResult(gen_time=gen.result, transfer_time=prep.result+get.result, operation_time=op.result)


def gen_sizes(max_size):
    sizes = np.random.randint(1, max_size+1, size=6).tolist()
    size = [sizes[0:4], sizes[1:5]]
    return size


class CuTensorTncontract(CuTensor):
    @classmethod
    def get_ready(self, num_tensors, *sizes):
        sizes = list(sizes)
        num_tensors += 1
        size_a = sizes[0][0]
        size_c = sizes[0][2]
        size_f = sizes[1][3]
        sizes.append([size_a, size_c, size_f])
        return num_tensors, *sizes


def main():

    experiment_group = "Angela_nslb_tncontract_random"

    contraction = 'abcd,bcdf->acf' # tensor

    # Backend
    backends = {
        'numpy':Numpy
        # , 'exatn': Exatn
    }
    if get_gpu_props_json():
        backends.update({
            'torch':TorchCuda
            , 'cupy':Cupy
            , 'cutensor': CuTensorTncontract
        })
    
    # Tensor properties
    num_tensors = 2
    dim = 4 # tensor
    # sizes = [2, 4, 8, 10, 16, 20, 30, 32, 40, 50, 60, 64, 70, 80, 100, 120, 128, 130, 150]  # tensor
    sizes = [10, 16, 20, 30, 32, 40, 50, 60, 64, 70, 80, 100, 120]  # tensor
    dtypes = ['float', 'double', 'complex64', 'complex128']

    # Test properties
    repeats = 5
    use_strip = True
    if use_strip:
        repeats += 2
    
    is_square = False
    
    # Bechmark
    for max_size in sizes:
        # max_size = 150  # hardcode
        results = []
        if is_square:
            input_sizes = [max_size for i in range(dim)] # square tensors
            size = [input_sizes, input_sizes]
        else:
            size = gen_sizes(max_size)

        for backend in backends:
            b = backends[backend]
            tncontractbench = TncontractBench()
        
            for dtype in dtypes:
                for _ in range(repeats):
                    _, bench_result = tncontractbench.benchmark(b,num_tensors, *size, dtype=dtype, contraction=contraction)
                    results.append(bench_result)
                json_result = tncontractbench.print_results_json(use_strip, backend, *size, dtype=dtype, results=results, experiment_group=experiment_group)      


if __name__ == "__main__":
    main()

