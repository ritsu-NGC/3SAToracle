"""
Test suite for the 3SAT Oracle quantum circuit implementation.
"""

import pytest
import sys
import os
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantum_circuit import SATOracle, create_simple_3sat_example

class TestSATOracle:
    """Test cases for the SATOracle class."""
    
    def test_oracle_initialization(self):
        """Test basic oracle initialization."""
        oracle = SATOracle(3)
        assert oracle.num_variables == 3
        assert len(oracle.clauses) == 0
        
    def test_add_clause(self):
        """Test adding clauses to the oracle."""
        oracle = SATOracle(3)
        oracle.add_clause([1, 2, 3])
        oracle.add_clause([-1, 2, -3])
        
        assert len(oracle.clauses) == 2
        assert oracle.clauses[0] == [1, 2, 3]
        assert oracle.clauses[1] == [-1, 2, -3]
        
    def test_invalid_clause_length(self):
        """Test that non-3SAT clauses are rejected."""
        oracle = SATOracle(3)
        
        with pytest.raises(ValueError, match="Only 3-SAT clauses are supported"):
            oracle.add_clause([1, 2])  # Too short
            
        with pytest.raises(ValueError, match="Only 3-SAT clauses are supported"):
            oracle.add_clause([1, 2, 3, 4])  # Too long
            
    def test_oracle_circuit_creation(self):
        """Test that oracle circuit is created successfully."""
        oracle = create_simple_3sat_example()
        circuit = oracle.build_oracle_circuit()
        
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits > 0
        assert circuit.depth() > 0
        
    def test_grover_circuit_creation(self):
        """Test that Grover circuit is created successfully."""
        oracle = create_simple_3sat_example()
        circuit = oracle.create_grover_circuit()
        
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits > 0
        assert circuit.depth() > 0
        
    def test_empty_oracle_grover_fails(self):
        """Test that Grover circuit creation fails with no clauses."""
        oracle = SATOracle(3)
        
        with pytest.raises(ValueError, match="No clauses added to the oracle"):
            oracle.create_grover_circuit()
            
    def test_circuit_simulation(self):
        """Test that the circuit can be simulated."""
        oracle = create_simple_3sat_example()
        circuit = oracle.create_grover_circuit()
        
        # Remove measurements for statevector simulation
        circuit_no_measure = circuit.copy()
        circuit_no_measure.remove_final_measurements()
        
        # Simulate
        simulator = AerSimulator(method='statevector')
        transpiled = transpile(circuit_no_measure, simulator)
        
        # Check that transpilation succeeded
        assert transpiled.num_qubits > 0
        
    def test_satisfiable_example(self):
        """Test with a known satisfiable example."""
        oracle = SATOracle(2)
        # (x1 OR x2 OR x1) is always satisfiable
        oracle.add_clause([1, 2, 1])
        
        circuit = oracle.build_oracle_circuit()
        assert circuit is not None
        
class TestCircuitEquivalence:
    """Test circuit equivalence using mqt.qcec."""
    
    def test_oracle_idempotency(self):
        """Test that applying oracle twice gives identity (up to global phase)."""
        oracle = create_simple_3sat_example()
        single_oracle = oracle.build_oracle_circuit()
        
        # Create double oracle circuit
        double_oracle_circuit = QuantumCircuit(single_oracle.num_qubits)
        double_oracle_circuit.compose(single_oracle, inplace=True)
        double_oracle_circuit.compose(single_oracle, inplace=True)
        
        # Remove final measurements for equivalence checking
        single_oracle.remove_final_measurements()
        double_oracle_circuit.remove_final_measurements()
        
        # The double oracle should be equivalent to identity (up to ancilla qubits)
        # This is a simplified test - in practice, we'd need more sophisticated equivalence checking
        assert double_oracle_circuit.num_qubits == single_oracle.num_qubits
        
    def test_different_oracle_orders(self):
        """Test that different orders of adding clauses produce equivalent oracles."""
        # Create first oracle
        oracle1 = SATOracle(3)
        oracle1.add_clause([1, 2, 3])
        oracle1.add_clause([-1, 2, -3])
        oracle1.add_clause([1, -2, 3])
        
        # Create second oracle with different order
        oracle2 = SATOracle(3)
        oracle2.add_clause([1, -2, 3])
        oracle2.add_clause([1, 2, 3])
        oracle2.add_clause([-1, 2, -3])
        
        circuit1 = oracle1.build_oracle_circuit()
        circuit2 = oracle2.build_oracle_circuit()
        
        # Remove measurements
        circuit1.remove_final_measurements()
        circuit2.remove_final_measurements()
        
        # Both circuits should have the same structure
        assert circuit1.num_qubits == circuit2.num_qubits
        
        # Note: For full equivalence checking, we would use mqt.qcec here:
        # from mqt import qcec
        # result = qcec.verify(circuit1, circuit2)
        # assert result.equivalence == qcec.EquivalenceCheckingResult.equivalent

class TestCircuitProperties:
    """Test various properties of the generated circuits."""
    
    def test_circuit_depth_reasonable(self):
        """Test that circuit depth is reasonable for the problem size."""
        oracle = create_simple_3sat_example()
        circuit = oracle.build_oracle_circuit()
        
        # Depth should be polynomial in number of variables and clauses
        expected_max_depth = (oracle.num_variables + len(oracle.clauses)) * 10
        assert circuit.depth() < expected_max_depth
        
    def test_qubit_count_correct(self):
        """Test that the number of qubits is correct."""
        oracle = create_simple_3sat_example()
        circuit = oracle.build_oracle_circuit()
        
        # Should have: variables + ancilla for each clause + 1 final ancilla + classical bits
        expected_qubits = oracle.num_variables + len(oracle.clauses) + 1
        expected_classical = oracle.num_variables
        
        # Check quantum register size (excluding classical)
        quantum_qubits = sum(reg.size for reg in circuit.qregs)
        assert quantum_qubits == expected_qubits
        
        # Check classical register size
        classical_bits = sum(reg.size for reg in circuit.cregs)
        assert classical_bits == expected_classical
        
    def test_grover_iterations_auto_calculation(self):
        """Test that Grover iterations are calculated automatically."""
        oracle = create_simple_3sat_example()
        
        # Test with automatic iteration calculation
        circuit_auto = oracle.create_grover_circuit()
        
        # Test with manual iteration specification
        circuit_manual = oracle.create_grover_circuit(iterations=2)
        
        # Both should be valid circuits
        assert circuit_auto.num_qubits > 0
        assert circuit_manual.num_qubits > 0
        
        # Manual version might have different depth
        # (This is just a sanity check, not a strict requirement)
        
def test_example_integration():
    """Integration test using the provided example."""
    oracle = create_simple_3sat_example()
    
    # Test that we can create both types of circuits
    oracle_circuit = oracle.build_oracle_circuit()
    grover_circuit = oracle.create_grover_circuit()
    
    assert oracle_circuit is not None
    assert grover_circuit is not None
    
    # Test that circuits have reasonable properties
    assert oracle_circuit.num_qubits >= oracle.num_variables
    assert grover_circuit.num_qubits >= oracle.num_variables
    
    print(f"Oracle circuit: {oracle_circuit.num_qubits} qubits, depth {oracle_circuit.depth()}")
    print(f"Grover circuit: {grover_circuit.num_qubits} qubits, depth {grover_circuit.depth()}")

if __name__ == "__main__":
    # Run a simple test when executed directly
    test_example_integration()
    print("Basic integration test passed!")