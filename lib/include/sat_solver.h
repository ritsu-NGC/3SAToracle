#ifndef SAT_SOLVER_H
#define SAT_SOLVER_H

#include <vector>
#include <string>

namespace sat_solver {

/**
 * A simple SAT solver library for demonstration purposes.
 * This provides classical SAT solving utilities that can complement
 * the quantum oracle approach.
 */
class SATSolver {
public:
    using Clause = std::vector<int>;
    using Formula = std::vector<Clause>;
    
    SATSolver();
    ~SATSolver();
    
    /**
     * Add a clause to the SAT formula.
     * @param clause Vector of literals (positive for variable, negative for negation)
     */
    void add_clause(const Clause& clause);
    
    /**
     * Clear all clauses from the formula.
     */
    void clear();
    
    /**
     * Get the number of variables in the formula.
     * @return Number of variables
     */
    int get_num_variables() const;
    
    /**
     * Get the number of clauses in the formula.
     * @return Number of clauses
     */
    int get_num_clauses() const;
    
    /**
     * Check if the current formula is satisfiable using a simple DPLL algorithm.
     * @return true if satisfiable, false otherwise
     */
    bool is_satisfiable();
    
    /**
     * Get a satisfying assignment if one exists.
     * @return Vector of boolean values for each variable (1-indexed)
     */
    std::vector<bool> get_satisfying_assignment();
    
    /**
     * Convert the formula to a string representation.
     * @return String representation of the formula
     */
    std::string to_string() const;
    
    /**
     * Validate that all clauses are 3-SAT clauses.
     * @return true if all clauses have exactly 3 literals
     */
    bool is_3sat() const;

private:
    Formula formula_;
    int num_variables_;
    std::vector<bool> assignment_;
    bool has_satisfying_assignment_;
    
    /**
     * Simple DPLL solver implementation.
     */
    bool dpll(Formula& formula, std::vector<bool>& assignment, int var);
    
    /**
     * Unit propagation step.
     */
    bool unit_propagate(Formula& formula, std::vector<bool>& assignment);
    
    /**
     * Pure literal elimination.
     */
    bool pure_literal_eliminate(Formula& formula, std::vector<bool>& assignment);
    
    /**
     * Choose next variable for branching.
     */
    int choose_variable(const Formula& formula);
    
    /**
     * Simplify formula given an assignment.
     */
    void simplify(Formula& formula, const std::vector<bool>& assignment);
};

/**
 * Utility functions for SAT manipulation.
 */
namespace utils {
    /**
     * Generate a random 3-SAT formula.
     * @param num_vars Number of variables
     * @param num_clauses Number of clauses
     * @return Random 3-SAT formula
     */
    SATSolver::Formula generate_random_3sat(int num_vars, int num_clauses);
    
    /**
     * Check if two formulas are equivalent.
     * @param f1 First formula
     * @param f2 Second formula
     * @return true if equivalent
     */
    bool are_equivalent(const SATSolver::Formula& f1, const SATSolver::Formula& f2);
}

} // namespace sat_solver

#endif // SAT_SOLVER_H