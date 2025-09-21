"""
Test suite for the SAT solver C++ library Python bindings.
"""

import pytest
import sys
import os

# Add src directory to path so we can import the compiled module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# This will only work after the C++ library is compiled
try:
    import sat_solver
    SAT_SOLVER_AVAILABLE = True
except ImportError:
    SAT_SOLVER_AVAILABLE = False
    sat_solver = None

@pytest.mark.skipif(not SAT_SOLVER_AVAILABLE, reason="SAT solver C++ library not compiled")
class TestSATSolver:
    """Test cases for the SAT solver C++ library."""
    
    def test_solver_initialization(self):
        """Test basic solver initialization."""
        solver = sat_solver.SATSolver()
        assert solver.get_num_variables() == 0
        assert solver.get_num_clauses() == 0
        
    def test_add_clause(self):
        """Test adding clauses to the solver."""
        solver = sat_solver.SATSolver()
        solver.add_clause([1, 2, 3])
        solver.add_clause([-1, 2, -3])
        
        assert solver.get_num_clauses() == 2
        assert solver.get_num_variables() == 3
        
    def test_satisfiable_formula(self):
        """Test with a satisfiable formula."""
        solver = sat_solver.SATSolver()
        
        # Simple satisfiable formula: (x1 OR x2 OR x3)
        solver.add_clause([1, 2, 3])
        
        assert solver.is_satisfiable() == True
        assignment = solver.get_satisfying_assignment()
        assert len(assignment) == 3
        
    def test_unsatisfiable_formula(self):
        """Test with an unsatisfiable formula."""
        solver = sat_solver.SATSolver()
        
        # Unsatisfiable formula: (x1) AND (NOT x1)
        solver.add_clause([1, 1, 1])
        solver.add_clause([-1, -1, -1])
        
        assert solver.is_satisfiable() == False
        assignment = solver.get_satisfying_assignment()
        assert len(assignment) == 0
        
    def test_3sat_validation(self):
        """Test 3-SAT validation."""
        solver = sat_solver.SATSolver()
        
        # Add 3-SAT clauses
        solver.add_clause([1, 2, 3])
        solver.add_clause([-1, 2, -3])
        
        assert solver.is_3sat() == True
        
    def test_clear_solver(self):
        """Test clearing the solver."""
        solver = sat_solver.SATSolver()
        solver.add_clause([1, 2, 3])
        
        assert solver.get_num_clauses() == 1
        
        solver.clear()
        assert solver.get_num_clauses() == 0
        assert solver.get_num_variables() == 0
        
    def test_string_representation(self):
        """Test string representation of formulas."""
        solver = sat_solver.SATSolver()
        solver.add_clause([1, 2, 3])
        solver.add_clause([-1, 2, -3])
        
        formula_str = solver.to_string()
        assert "x1" in formula_str
        assert "x2" in formula_str
        assert "x3" in formula_str
        assert "OR" in formula_str
        assert "AND" in formula_str
        
    def test_solver_repr(self):
        """Test the __repr__ method."""
        solver = sat_solver.SATSolver()
        solver.add_clause([1, 2, 3])
        
        repr_str = repr(solver)
        assert "SATSolver" in repr_str
        assert "1 clauses" in repr_str
        assert "3 variables" in repr_str

@pytest.mark.skipif(not SAT_SOLVER_AVAILABLE, reason="SAT solver C++ library not compiled")
class TestSATSolverUtils:
    """Test utility functions."""
    
    def test_random_3sat_generation(self):
        """Test random 3-SAT formula generation."""
        formula = sat_solver.utils.generate_random_3sat(3, 5)
        
        assert len(formula) == 5  # 5 clauses
        
        for clause in formula:
            assert len(clause) == 3  # Each clause has 3 literals
            
        # Test with solver
        solver = sat_solver.SATSolver()
        for clause in formula:
            solver.add_clause(clause)
            
        assert solver.get_num_clauses() == 5
        assert solver.is_3sat() == True
        
    def test_create_solver_from_clauses(self):
        """Test convenience function for creating solver from clauses."""
        clauses = [[1, 2, 3], [-1, 2, -3], [1, -2, 3]]
        solver = sat_solver.create_solver_from_clauses(clauses)
        
        assert solver.get_num_clauses() == 3
        assert solver.get_num_variables() == 3
        assert solver.is_3sat() == True

@pytest.mark.skipif(not SAT_SOLVER_AVAILABLE, reason="SAT solver C++ library not compiled")
class TestSATSolverIntegration:
    """Integration tests combining quantum and classical SAT solving."""
    
    def test_same_formula_both_solvers(self):
        """Test the same formula with both quantum oracle and classical solver."""
        # Define a simple 3-SAT formula
        clauses = [[1, 2, 3], [-1, 2, -3], [1, -2, 3]]
        
        # Classical solver
        classical_solver = sat_solver.SATSolver()
        for clause in clauses:
            classical_solver.add_clause(clause)
            
        classical_satisfiable = classical_solver.is_satisfiable()
        
        # Quantum oracle (if available)
        try:
            from quantum_circuit import SATOracle
            quantum_oracle = SATOracle(3)
            for clause in clauses:
                quantum_oracle.add_clause(clause)
                
            # Both should agree on the same formula structure
            assert len(quantum_oracle.clauses) == classical_solver.get_num_clauses()
            assert quantum_oracle.num_variables == classical_solver.get_num_variables()
            
        except ImportError:
            # If quantum circuit module is not available, just test classical
            pass
            
        # Classical solver should be able to solve it
        if classical_satisfiable:
            assignment = classical_solver.get_satisfying_assignment()
            assert len(assignment) == 3

def test_sat_solver_availability():
    """Test to check if SAT solver library is available."""
    if SAT_SOLVER_AVAILABLE:
        print("SAT solver C++ library is available")
        print(f"Version: {sat_solver.__version__}")
    else:
        print("SAT solver C++ library not available - needs to be compiled")
        print("Run 'cmake --build build' to compile the library")

if __name__ == "__main__":
    # Run availability test when executed directly
    test_sat_solver_availability()
    
    if SAT_SOLVER_AVAILABLE:
        # Run a simple integration test
        solver = sat_solver.SATSolver()
        solver.add_clause([1, 2, 3])
        print(f"Created solver with {solver.get_num_clauses()} clauses")
        print("SAT solver integration test passed!")
    else:
        print("Skipping integration test - library not available")