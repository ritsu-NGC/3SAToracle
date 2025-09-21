"""
3SAT Oracle Package

A hybrid quantum-classical approach to solving 3-SAT problems.
"""

from .quantum_circuit import SATOracle, create_simple_3sat_example

__version__ = "1.0.0"
__author__ = "3SAT Oracle Team"
__description__ = "Quantum-classical 3-SAT solver"

__all__ = [
    "SATOracle",
    "create_simple_3sat_example",
]