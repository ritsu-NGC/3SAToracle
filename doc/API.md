# 3SAT Oracle API Documentation

## Overview

The 3SAT Oracle project provides both quantum and classical approaches to solving 3-SAT (3-satisfiability) problems. It combines:

- **Quantum Circuit Implementation**: Using Qiskit to create Grover's algorithm-based quantum oracles
- **Classical SAT Solver**: A C++ library with Python bindings for traditional DPLL-based solving
- **Testing Framework**: Comprehensive tests including quantum circuit equivalence checking

## Core Components

### Quantum Circuit Module (`src/quantum_circuit.py`)

#### SATOracle Class

The main class for creating quantum oracles for 3-SAT problems.

```python
from quantum_circuit import SATOracle, create_simple_3sat_example

# Create an oracle for 3 variables
oracle = SATOracle(3)

# Add 3-SAT clauses (e.g., x1 OR x2 OR x3)
oracle.add_clause([1, 2, 3])      # Positive literals
oracle.add_clause([-1, 2, -3])   # Negative literals (NOT x1 OR x2 OR NOT x3)

# Build the quantum oracle circuit
oracle_circuit = oracle.build_oracle_circuit()

# Create a complete Grover algorithm circuit
grover_circuit = oracle.create_grover_circuit()
```

#### Key Methods

- `add_clause(clause)`: Add a 3-SAT clause as a list of literals
- `build_oracle_circuit()`: Create the quantum oracle circuit
- `create_grover_circuit(iterations=None)`: Create complete Grover's algorithm circuit
- `create_simple_3sat_example()`: Helper function for creating test instances

### Classical SAT Solver (`lib/`)

#### C++ Library

The C++ library provides efficient classical SAT solving using the DPLL algorithm.

**Header**: `lib/include/sat_solver.h`
**Implementation**: `lib/src/sat_solver.cpp`
**Python Bindings**: `lib/src/python_bindings.cpp`

#### Python Interface

```python
import sat_solver

# Create a solver
solver = sat_solver.SATSolver()

# Add clauses
solver.add_clause([1, 2, 3])
solver.add_clause([-1, 2, -3])

# Check satisfiability
if solver.is_satisfiable():
    assignment = solver.get_satisfying_assignment()
    print(f"Satisfying assignment: {assignment}")
else:
    print("Formula is unsatisfiable")

# Utility functions
random_formula = sat_solver.utils.generate_random_3sat(num_vars=5, num_clauses=10)
```

#### Key Methods

- `add_clause(clause)`: Add a clause to the formula
- `is_satisfiable()`: Check if the formula is satisfiable
- `get_satisfying_assignment()`: Get a satisfying assignment if one exists
- `clear()`: Clear all clauses
- `is_3sat()`: Validate that all clauses are 3-SAT clauses
- `to_string()`: Get string representation of the formula

### Testing Framework (`test/`)

#### Test Modules

1. **`test_quantum_circuit.py`**: Tests for quantum circuit implementation
2. **`test_sat_solver.py`**: Tests for C++ SAT solver library
3. **`test_equivalence.py`**: Quantum circuit equivalence tests using mqt.qcec

#### Running Tests

```bash
# Run all tests
pytest test/ -v

# Run specific test categories
pytest test/test_quantum_circuit.py -v
pytest test/test_sat_solver.py -v
pytest test/test_equivalence.py -v

# Skip tests that require external libraries
pytest test/ -m "not requires_qcec and not requires_cpp"
```

## Example Usage

### Complete 3-SAT Example

```python
from quantum_circuit import SATOracle
import sat_solver

# Define a 3-SAT problem: (x1 OR x2 OR x3) AND (NOT x1 OR x2 OR NOT x3)
clauses = [[1, 2, 3], [-1, 2, -3]]

# Classical approach
classical_solver = sat_solver.SATSolver()
for clause in clauses:
    classical_solver.add_clause(clause)

print(f"Classical solver: Satisfiable = {classical_solver.is_satisfiable()}")
if classical_solver.is_satisfiable():
    print(f"Assignment: {classical_solver.get_satisfying_assignment()}")

# Quantum approach
quantum_oracle = SATOracle(3)
for clause in clauses:
    quantum_oracle.add_clause(clause)

oracle_circuit = quantum_oracle.build_oracle_circuit()
grover_circuit = quantum_oracle.create_grover_circuit()

print(f"Quantum oracle: {oracle_circuit.num_qubits} qubits, depth {oracle_circuit.depth()}")
print(f"Grover circuit: {grover_circuit.num_qubits} qubits, depth {grover_circuit.depth()}")
```

### Circuit Simulation

```python
from qiskit import transpile
from qiskit_aer import AerSimulator

# Create and simulate the circuit
oracle = create_simple_3sat_example()
circuit = oracle.create_grover_circuit()

# Simulate on quantum simulator
simulator = AerSimulator()
transpiled_circuit = transpile(circuit, simulator)
job = simulator.run(transpiled_circuit, shots=1000)
result = job.result()
counts = result.get_counts()

print(f"Measurement results: {counts}")
```

## Dependencies

### Python Packages

- `qiskit`: Quantum circuit construction and simulation
- `qiskit-aer`: Quantum simulator backend
- `pytest`: Testing framework
- `numpy`: Numerical computations
- `pybind11`: C++/Python bindings
- `mqt.qcec`: Quantum circuit equivalence checking (optional)

### C++ Dependencies

- **CMake** (≥ 3.12): Build system
- **C++17** compatible compiler
- **pybind11**: For Python bindings

## Performance Notes

- **Quantum Oracle**: Circuit depth grows linearly with number of clauses
- **Classical Solver**: DPLL algorithm, exponential worst-case but efficient in practice
- **Memory Usage**: Quantum circuits require exponential classical memory for simulation
- **Grover Iterations**: Automatically calculated as π/4 × √N for N = 2^(num_variables)

## Limitations

1. **Quantum Simulation**: Limited to small numbers of variables due to exponential resource requirements
2. **Circuit Depth**: Deep circuits may be noisy on real quantum hardware
3. **Equivalence Checking**: mqt.qcec may not be available in all environments
4. **3-SAT Only**: Current implementation specifically targets 3-SAT problems

## Future Extensions

- Support for general k-SAT problems
- Quantum error correction integration
- Hardware-specific transpilation optimizations
- Advanced classical preprocessing techniques