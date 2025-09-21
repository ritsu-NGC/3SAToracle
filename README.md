# 3SAT Oracle

A hybrid quantum-classical approach to solving 3-SAT (3-satisfiability) problems, combining Qiskit-based quantum oracles with classical DPLL solving algorithms.

## Features

- **Quantum Oracle Implementation**: Grover's algorithm-based quantum oracle for 3-SAT problems using Qiskit
- **Classical SAT Solver**: High-performance C++ DPLL-based solver with Python bindings
- **Comprehensive Testing**: pytest-based test suite with quantum circuit equivalence checking using mqt.qcec
- **Cross-Platform Build System**: CMake-based build system for C++ library and Python integration

## Project Structure

```
3SAToracle/
├── src/               # Python quantum circuit implementation
│   └── quantum_circuit.py
├── lib/               # C++ SAT solver library
│   ├── include/       # Header files
│   ├── src/           # C++ implementation and Python bindings
│   └── CMakeLists.txt
├── test/              # Test suite
│   ├── test_quantum_circuit.py
│   ├── test_sat_solver.py
│   └── test_equivalence.py
├── doc/               # Documentation
│   └── API.md
├── CMakeLists.txt     # Top-level build configuration
└── README.md          # This file
```

## Installation Guide

### Prerequisites

#### System Requirements
- **Python 3.8+**
- **CMake 3.12+**
- **C++17 compatible compiler** (GCC 7+, Clang 7+, MSVC 2019+)
- **Git** (for cloning the repository)

#### Operating System Support
- Linux (Ubuntu 18.04+, CentOS 7+)
- macOS (10.14+)
- Windows (with Visual Studio 2019+ or MinGW)

### Step 1: Clone the Repository

```bash
git clone https://github.com/ritsu-NGC/3SAToracle.git
cd 3SAToracle
```

### Step 2: Install Python Dependencies

```bash
# Install core dependencies
pip install qiskit qiskit-aer numpy pytest pybind11

# Install optional dependencies for advanced features
pip install mqt.qcec  # For quantum circuit equivalence checking
```

### Step 3: Build the C++ Library

#### Option A: Using CMake (Recommended)

```bash
# Create build directory
mkdir build
cd build

# Configure the build
cmake ..

# Install Python dependencies (optional, can also be done manually)
cmake --build . --target install_python_deps

# Build the project
cmake --build . --config Release

# This will:
# 1. Compile the C++ SAT solver library
# 2. Build Python bindings using pybind11
# 3. Copy the compiled module to src/ directory
```

#### Option B: Manual Build (Advanced Users)

```bash
# Build only the C++ library
cd lib
mkdir build
cd build
cmake ..
cmake --build . --config Release

# Copy the generated Python module to src/
cp sat_solver*.so ../../src/  # Linux/macOS
# or
cp sat_solver*.pyd ../../src/  # Windows
```

### Step 4: Verify Installation

```bash
# Run basic tests to verify everything works
cd /path/to/3SAToracle  # Return to project root
python -c "
from src.quantum_circuit import create_simple_3sat_example
oracle = create_simple_3sat_example()
circuit = oracle.build_oracle_circuit()
print(f'✓ Quantum circuit created: {circuit.num_qubits} qubits')

try:
    from src import sat_solver
    solver = sat_solver.SATSolver()
    solver.add_clause([1, 2, 3])
    print(f'✓ Classical solver working: {solver.is_satisfiable()}')
except ImportError:
    print('⚠ Classical solver not compiled - run cmake build')
"
```

### Step 5: Run the Test Suite

```bash
# Run all tests
pytest test/ -v

# Run tests without optional dependencies
pytest test/ -m "not requires_qcec and not requires_cpp" -v

# Run specific test categories
pytest test/test_quantum_circuit.py -v  # Quantum circuit tests
pytest test/test_sat_solver.py -v       # Classical solver tests (requires compilation)
pytest test/test_equivalence.py -v      # Equivalence checking (requires mqt.qcec)
```

## Quick Start

### Example 1: Basic 3-SAT Problem

```python
from src.quantum_circuit import SATOracle

# Create a 3-SAT oracle for 3 variables
oracle = SATOracle(3)

# Add clauses: (x1 OR x2 OR x3) AND (NOT x1 OR x2 OR NOT x3)
oracle.add_clause([1, 2, 3])      # x1 OR x2 OR x3
oracle.add_clause([-1, 2, -3])    # NOT x1 OR x2 OR NOT x3

# Build quantum oracle circuit
quantum_circuit = oracle.build_oracle_circuit()
print(f"Oracle circuit: {quantum_circuit.num_qubits} qubits, depth {quantum_circuit.depth()}")

# Create complete Grover's algorithm circuit
grover_circuit = oracle.create_grover_circuit()
print(f"Grover circuit: {grover_circuit.num_qubits} qubits, depth {grover_circuit.depth()}")
```

### Example 2: Classical SAT Solving

```python
from src import sat_solver  # Requires compilation

# Create classical solver
solver = sat_solver.SATSolver()

# Add the same clauses
solver.add_clause([1, 2, 3])
solver.add_clause([-1, 2, -3])

# Solve classically
if solver.is_satisfiable():
    assignment = solver.get_satisfying_assignment()
    print(f"Satisfying assignment: {assignment}")
    print(f"Formula: {solver.to_string()}")
else:
    print("Formula is unsatisfiable")
```

### Example 3: Circuit Simulation

```python
from qiskit import transpile
from qiskit_aer import AerSimulator
from src.quantum_circuit import create_simple_3sat_example

# Create example circuit
oracle = create_simple_3sat_example()
circuit = oracle.create_grover_circuit()

# Simulate
simulator = AerSimulator()
transpiled = transpile(circuit, simulator)
job = simulator.run(transpiled, shots=1000)
result = job.result()
counts = result.get_counts()

print(f"Measurement results: {counts}")
```

## CMake Build Targets

The project provides several CMake targets:

```bash
# Build everything
cmake --build . --target all

# Build only the C++ library
cmake --build . --target sat_solver_lib

# Build only Python bindings
cmake --build . --target sat_solver_py

# Install Python dependencies
cmake --build . --target install_python_deps

# Run tests (after building)
cmake --build . --target run_tests
```

## Troubleshooting

### Common Issues

#### 1. Python Module Import Error
```bash
ImportError: No module named 'sat_solver'
```
**Solution**: The C++ library hasn't been compiled. Run `cmake --build build --config Release` to build it.

#### 2. CMake Configuration Fails
```bash
CMake Error: Could not find pybind11
```
**Solution**: Install pybind11: `pip install pybind11`

#### 3. Compiler Errors on Windows
**Solution**: Ensure you have Visual Studio 2019+ or MinGW with C++17 support installed.

#### 4. Qiskit Import Errors
```bash
ImportError: No module named 'qiskit'
```
**Solution**: Install Qiskit: `pip install qiskit qiskit-aer`

#### 5. mqt.qcec Not Available
```bash
ImportError: No module named 'mqt.qcec'
```
**Solution**: This is optional. Install with `pip install mqt.qcec` or run tests with `-m "not requires_qcec"`

### Platform-Specific Notes

#### Linux
- Ensure you have `build-essential` package: `sudo apt-get install build-essential cmake`
- For older distributions, you may need to install a newer CMake

#### macOS
- Install Xcode command line tools: `xcode-select --install`
- Consider using Homebrew: `brew install cmake`

#### Windows
- Use Visual Studio 2019+ or Visual Studio Code with C++ extension
- Consider using vcpkg for dependency management
- Ensure Python is added to PATH

## Performance and Limitations

### Quantum Simulation Limits
- **Variables**: Practical limit ~15-20 qubits due to exponential memory requirements
- **Circuit Depth**: Deep circuits may be challenging for NISQ devices
- **Simulation Time**: Exponential scaling with number of qubits

### Classical Solver Performance
- **Small Problems**: Very fast (< 1ms)
- **Large Problems**: Performance depends on problem structure
- **Memory Usage**: Linear in formula size

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run the test suite: `pytest test/ -v`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- **Grover's Algorithm**: L. K. Grover, "A fast quantum mechanical algorithm for database search," 1996
- **3-SAT Problem**: Classic NP-complete problem in computational complexity theory
- **Qiskit**: Open-source quantum computing framework by IBM
- **DPLL Algorithm**: Davis-Putnam-Logemann-Loveland SAT solving algorithm

## Acknowledgments

- IBM Qiskit team for the quantum computing framework
- pybind11 developers for C++/Python integration
- mqt.qcec team for quantum circuit equivalence checking tools