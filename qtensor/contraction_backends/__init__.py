#from torch._C import device
from .base_class import ContractionBackend
from .numpy import NumpyBackend
from .torch import TorchBackend
from .cupy import CuPyBackend
from .mkl import CMKLExtendedBackend
from .cupy import CuPyBackend
from .cutensor import CuTensorBackend
from .transposed import TransposedBackend
from .opt_einsum import OptEinusmBackend
from .transpose_backend import NumpyTranspoedBackend, TorchTransposedBackend, CupyTransposedBackend, CutensorTransposedBackend
from .performance_measurement_decorator import PerfNumpyBackend, PerfBackend, GPUPerfBackend

def get_backend(name):
    backend_dict = {
        'mkl': CMKLExtendedBackend,
        'einsum':NumpyBackend,
        'opt_einsum': OptEinusmBackend,
        'torch_cpu': TorchBackend,
        'torch_gpu': TorchBackend,
        'cupy': CuPyBackend,
        'cutensor': CuTensorBackend,
        'tr_einsum': NumpyTranspoedBackend,
        'tr_torch': TorchTransposedBackend,
        'tr_cupy': CupyTransposedBackend,
        'tr_cutensor': CutensorTransposedBackend
    }[name]()
    if name in ["torch_gpu", "tr_torch"]:
        return backend_dict['torch'](device = name[-3:])
    else:
        return backend_dict[name]()

def get_cpu_perf_backend(name):
    class MyPerfBackend(PerfBackend):
        Backend = {
            'mkl': CMKLExtendedBackend,
            'einsum':NumpyBackend,
            'opt_einsum': OptEinusmBackend,
            'torch_cpu': TorchBackend,     
            'tr_einsum': NumpyTranspoedBackend,
        }[name]

    return MyPerfBackend()

def get_gpu_perf_backend(name):
    class MyPerfBackend(GPUPerfBackend):
        Backend = {
            'torch_gpu': TorchBackend,
            'cupy': CuPyBackend,
            'cutensor': CuTensorBackend,
            'tr_torch': TorchTransposedBackend,
            'tr_cupy': CupyTransposedBackend,
            'tr_cutensor': CutensorTransposedBackend
        }[name]

    if name == "torch_gpu":
        return MyPerfBackend(device="gpu")
    else:
        return MyPerfBackend()
