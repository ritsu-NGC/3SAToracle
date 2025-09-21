"""
Quantum circuit implementation for 3SAT oracle using Qiskit.
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from typing import List, Tuple
import numpy as np


class SATOracle:
    """
    Quantum oracle for 3-SAT problems using Qiskit.
    """
    
    def __init__(self, num_variables: int):
        """
        Initialize the SAT oracle.
        
        Args:
            num_variables: Number of variables in the SAT problem
        """
        self.num_variables = num_variables
        self.clauses = []
        self.circuit = None
        
    def add_clause(self, clause: List[int]):
        """
        Add a 3-SAT clause to the oracle.
        
        Args:
            clause: List of literals (positive for variable, negative for negation)
        """
        if len(clause) != 3:
            raise ValueError("Only 3-SAT clauses are supported")
        self.clauses.append(clause)
        
    def build_oracle_circuit(self) -> QuantumCircuit:
        """
        Build the quantum oracle circuit for the 3-SAT problem.
        
        Returns:
            QuantumCircuit: The oracle circuit
        """
        # Create quantum and classical registers
        qreg = QuantumRegister(self.num_variables, 'q')
        ancilla = QuantumRegister(len(self.clauses) + 1, 'ancilla')
        creg = ClassicalRegister(self.num_variables, 'c')
        
        circuit = QuantumCircuit(qreg, ancilla, creg)
        
        # Initialize superposition of all possible assignments
        circuit.h(qreg)
        
        # Apply oracle for each clause
        for i, clause in enumerate(self.clauses):
            self._apply_clause_oracle(circuit, qreg, ancilla[i], clause)
            
        # Final oracle bit
        circuit.mcx(ancilla[:-1], ancilla[-1])
        
        # Phase flip for satisfying assignments
        circuit.z(ancilla[-1])
        
        # Uncompute ancilla qubits
        circuit.mcx(ancilla[:-1], ancilla[-1])
        
        for i, clause in enumerate(reversed(self.clauses)):
            self._unapply_clause_oracle(circuit, qreg, ancilla[len(self.clauses)-1-i], clause)
            
        self.circuit = circuit
        return circuit
        
    def _apply_clause_oracle(self, circuit: QuantumCircuit, qreg: QuantumRegister, 
                           ancilla: int, clause: List[int]):
        """
        Apply oracle for a single clause.
        """
        # For clause (x1 OR x2 OR x3), we want ancilla = NOT(NOT x1 AND NOT x2 AND NOT x3)
        
        # Get unique variables and their polarities
        unique_vars = {}  # var_idx -> is_negative
        for literal in clause:
            var_idx = abs(literal) - 1
            is_negative = literal < 0
            # If we see the same variable multiple times, OR the polarities
            # (x OR NOT x) = True, so we can simplify
            if var_idx in unique_vars:
                if unique_vars[var_idx] != is_negative:
                    # We have both x and NOT x, so the clause is always true
                    circuit.x(ancilla)  # Set ancilla to True
                    return
            else:
                unique_vars[var_idx] = is_negative
        
        # Apply X gates for negative literals
        for var_idx, is_negative in unique_vars.items():
            if is_negative:
                circuit.x(qreg[var_idx])
        
        # Build controls list (no duplicates)
        controls = [qreg[var_idx] for var_idx in unique_vars.keys()]
            
        # Apply multi-controlled NOT
        if len(controls) > 0:
            circuit.mcx(controls, ancilla)
            circuit.x(ancilla)  # Flip to get OR result
        else:
            # Empty controls, set ancilla to True
            circuit.x(ancilla)
        
        # Unflip negative literals
        for var_idx, is_negative in unique_vars.items():
            if is_negative:
                circuit.x(qreg[var_idx])
                
    def _unapply_clause_oracle(self, circuit: QuantumCircuit, qreg: QuantumRegister,
                             ancilla: int, clause: List[int]):
        """
        Unapply oracle for a single clause (reverse operations).
        """
        # Get unique variables and their polarities (same logic as apply)
        unique_vars = {}
        for literal in clause:
            var_idx = abs(literal) - 1
            is_negative = literal < 0
            if var_idx in unique_vars:
                if unique_vars[var_idx] != is_negative:
                    # We have both x and NOT x, clause was always true
                    circuit.x(ancilla)  # Unset ancilla from True
                    return
            else:
                unique_vars[var_idx] = is_negative
        
        # Unflip negative literals first
        for var_idx, is_negative in unique_vars.items():
            if is_negative:
                circuit.x(qreg[var_idx])
                
        # Build controls list (no duplicates)
        controls = [qreg[var_idx] for var_idx in unique_vars.keys()]
        
        if len(controls) > 0:
            circuit.x(ancilla)  # Unflip
            circuit.mcx(controls, ancilla)
        else:
            circuit.x(ancilla)  # Just unflip if no controls
        
        # Re-flip negative literals to restore original state
        for var_idx, is_negative in unique_vars.items():
            if is_negative:
                circuit.x(qreg[var_idx])
        
    def create_grover_circuit(self, iterations: int = None) -> QuantumCircuit:
        """
        Create a complete Grover's algorithm circuit for the 3-SAT problem.
        
        Args:
            iterations: Number of Grover iterations (auto-calculated if None)
            
        Returns:
            QuantumCircuit: Complete Grover circuit
        """
        if not self.clauses:
            raise ValueError("No clauses added to the oracle")
            
        if iterations is None:
            # Optimal number of iterations for Grover's algorithm
            N = 2 ** self.num_variables
            iterations = int(np.pi / 4 * np.sqrt(N))
            
        oracle = self.build_oracle_circuit()
        
        # Create diffusion operator (amplitude amplification about average)
        qreg = QuantumRegister(self.num_variables, 'q')
        ancilla = QuantumRegister(len(self.clauses) + 1, 'ancilla')
        creg = ClassicalRegister(self.num_variables, 'c')
        
        grover_circuit = QuantumCircuit(qreg, ancilla, creg)
        
        # Initial superposition
        grover_circuit.h(qreg)
        
        # Grover iterations
        for _ in range(iterations):
            # Apply oracle
            grover_circuit.compose(oracle, inplace=True)
            
            # Apply diffusion operator
            grover_circuit.h(qreg)
            grover_circuit.x(qreg)
            grover_circuit.h(qreg[-1])
            grover_circuit.mcx(qreg[:-1], qreg[-1])
            grover_circuit.h(qreg[-1])
            grover_circuit.x(qreg)
            grover_circuit.h(qreg)
            
        # Measure
        grover_circuit.measure(qreg, creg)
        
        return grover_circuit


def create_simple_3sat_example() -> SATOracle:
    """
    Create a simple 3-SAT example for testing.
    
    Returns:
        SATOracle: Configured oracle with example clauses
    """
    oracle = SATOracle(3)  # 3 variables: x1, x2, x3
    
    # Example: (x1 OR x2 OR x3) AND (NOT x1 OR x2 OR NOT x3) AND (x1 OR NOT x2 OR x3)
    oracle.add_clause([1, 2, 3])      # x1 OR x2 OR x3
    oracle.add_clause([-1, 2, -3])   # NOT x1 OR x2 OR NOT x3
    oracle.add_clause([1, -2, 3])    # x1 OR NOT x2 OR x3
    
    return oracle


if __name__ == "__main__":
    # Example usage
    oracle = create_simple_3sat_example()
    circuit = oracle.create_grover_circuit()
    
    print(f"Created Grover circuit with {circuit.num_qubits} qubits")
    print(f"Circuit depth: {circuit.depth()}")
    print(f"Number of clauses: {len(oracle.clauses)}")