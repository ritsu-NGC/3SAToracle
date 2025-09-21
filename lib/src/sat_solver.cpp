#include "sat_solver.h"
#include <algorithm>
#include <random>
#include <sstream>
#include <set>

namespace sat_solver {

SATSolver::SATSolver() : num_variables_(0), has_satisfying_assignment_(false) {}

SATSolver::~SATSolver() {}

void SATSolver::add_clause(const Clause& clause) {
    formula_.push_back(clause);
    
    // Update number of variables
    for (int lit : clause) {
        int var = std::abs(lit);
        if (var > num_variables_) {
            num_variables_ = var;
        }
    }
    
    // Reset satisfying assignment since formula changed
    has_satisfying_assignment_ = false;
    assignment_.clear();
}

void SATSolver::clear() {
    formula_.clear();
    num_variables_ = 0;
    assignment_.clear();
    has_satisfying_assignment_ = false;
}

int SATSolver::get_num_variables() const {
    return num_variables_;
}

int SATSolver::get_num_clauses() const {
    return formula_.size();
}

bool SATSolver::is_satisfiable() {
    if (formula_.empty()) {
        return true;
    }
    
    // Reset assignment
    assignment_.assign(num_variables_ + 1, false);  // 1-indexed
    has_satisfying_assignment_ = false;
    
    // Make a copy of the formula for DPLL
    Formula formula_copy = formula_;
    
    bool result = dpll(formula_copy, assignment_, 1);
    has_satisfying_assignment_ = result;
    
    return result;
}

std::vector<bool> SATSolver::get_satisfying_assignment() {
    if (!has_satisfying_assignment_) {
        if (!is_satisfiable()) {
            return std::vector<bool>();
        }
    }
    
    // Return assignment without index 0 (since we use 1-indexing)
    std::vector<bool> result(assignment_.begin() + 1, assignment_.end());
    return result;
}

std::string SATSolver::to_string() const {
    std::ostringstream oss;
    
    for (size_t i = 0; i < formula_.size(); ++i) {
        oss << "(";
        for (size_t j = 0; j < formula_[i].size(); ++j) {
            if (j > 0) oss << " OR ";
            
            int lit = formula_[i][j];
            if (lit < 0) {
                oss << "NOT x" << (-lit);
            } else {
                oss << "x" << lit;
            }
        }
        oss << ")";
        
        if (i < formula_.size() - 1) {
            oss << " AND ";
        }
    }
    
    return oss.str();
}

bool SATSolver::is_3sat() const {
    for (const auto& clause : formula_) {
        if (clause.size() != 3) {
            return false;
        }
    }
    return true;
}

bool SATSolver::dpll(Formula& formula, std::vector<bool>& assignment, int var) {
    // Base case: if formula is empty, it's satisfied
    if (formula.empty()) {
        return true;
    }
    
    // Check for empty clauses (unsatisfiable)
    for (const auto& clause : formula) {
        if (clause.empty()) {
            return false;
        }
    }
    
    // Unit propagation
    if (unit_propagate(formula, assignment)) {
        return false;  // Conflict found
    }
    
    // Pure literal elimination
    pure_literal_eliminate(formula, assignment);
    
    // If formula is empty after simplification, it's satisfied
    if (formula.empty()) {
        return true;
    }
    
    // Choose next variable
    int next_var = choose_variable(formula);
    if (next_var == -1) {
        return true;  // No more variables to assign
    }
    
    // Try assigning true
    assignment[next_var] = true;
    Formula formula_copy = formula;
    simplify(formula_copy, assignment);
    
    if (dpll(formula_copy, assignment, next_var + 1)) {
        return true;
    }
    
    // Try assigning false
    assignment[next_var] = false;
    formula_copy = formula;
    simplify(formula_copy, assignment);
    
    return dpll(formula_copy, assignment, next_var + 1);
}

bool SATSolver::unit_propagate(Formula& formula, std::vector<bool>& assignment) {
    bool changed = true;
    
    while (changed) {
        changed = false;
        
        for (auto it = formula.begin(); it != formula.end();) {
            if (it->size() == 1) {
                // Unit clause found
                int lit = (*it)[0];
                int var = std::abs(lit);
                bool value = lit > 0;
                
                assignment[var] = value;
                
                // Remove satisfied clauses and literals
                simplify(formula, assignment);
                
                changed = true;
                break;  // Start over since formula changed
            } else {
                ++it;
            }
        }
    }
    
    // Check for conflicts (empty clauses)
    for (const auto& clause : formula) {
        if (clause.empty()) {
            return true;  // Conflict
        }
    }
    
    return false;  // No conflict
}

bool SATSolver::pure_literal_eliminate(Formula& formula, std::vector<bool>& assignment) {
    std::set<int> positive_literals, negative_literals;
    
    // Collect all literals
    for (const auto& clause : formula) {
        for (int lit : clause) {
            if (lit > 0) {
                positive_literals.insert(lit);
            } else {
                negative_literals.insert(-lit);
            }
        }
    }
    
    // Find pure literals
    for (int var : positive_literals) {
        if (negative_literals.find(var) == negative_literals.end()) {
            // Pure positive literal
            assignment[var] = true;
            simplify(formula, assignment);
            return true;
        }
    }
    
    for (int var : negative_literals) {
        if (positive_literals.find(var) == positive_literals.end()) {
            // Pure negative literal
            assignment[var] = false;
            simplify(formula, assignment);
            return true;
        }
    }
    
    return false;
}

int SATSolver::choose_variable(const Formula& formula) {
    std::set<int> unassigned_vars;
    
    for (const auto& clause : formula) {
        for (int lit : clause) {
            unassigned_vars.insert(std::abs(lit));
        }
    }
    
    if (unassigned_vars.empty()) {
        return -1;
    }
    
    return *unassigned_vars.begin();
}

void SATSolver::simplify(Formula& formula, const std::vector<bool>& assignment) {
    for (auto clause_it = formula.begin(); clause_it != formula.end();) {
        bool clause_satisfied = false;
        
        for (auto lit_it = clause_it->begin(); lit_it != clause_it->end();) {
            int lit = *lit_it;
            int var = std::abs(lit);
            bool var_value = assignment[var];
            
            if ((lit > 0 && var_value) || (lit < 0 && !var_value)) {
                // Literal is satisfied, entire clause is satisfied
                clause_satisfied = true;
                break;
            } else if ((lit > 0 && !var_value) || (lit < 0 && var_value)) {
                // Literal is falsified, remove it from clause
                lit_it = clause_it->erase(lit_it);
            } else {
                ++lit_it;
            }
        }
        
        if (clause_satisfied) {
            // Remove satisfied clause
            clause_it = formula.erase(clause_it);
        } else {
            ++clause_it;
        }
    }
}

namespace utils {

SATSolver::Formula generate_random_3sat(int num_vars, int num_clauses) {
    SATSolver::Formula formula;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> var_dist(1, num_vars);
    std::uniform_int_distribution<> sign_dist(0, 1);
    
    for (int i = 0; i < num_clauses; ++i) {
        SATSolver::Clause clause;
        
        for (int j = 0; j < 3; ++j) {
            int var = var_dist(gen);
            bool positive = sign_dist(gen);
            
            clause.push_back(positive ? var : -var);
        }
        
        formula.push_back(clause);
    }
    
    return formula;
}

bool are_equivalent(const SATSolver::Formula& f1, const SATSolver::Formula& f2) {
    SATSolver solver1, solver2;
    
    for (const auto& clause : f1) {
        solver1.add_clause(clause);
    }
    
    for (const auto& clause : f2) {
        solver2.add_clause(clause);
    }
    
    bool sat1 = solver1.is_satisfiable();
    bool sat2 = solver2.is_satisfiable();
    
    if (sat1 != sat2) {
        return false;
    }
    
    if (!sat1) {
        return true;  // Both unsatisfiable
    }
    
    // For a more thorough check, we would need to enumerate all satisfying assignments
    // This is a simplified equivalence check
    return true;
}

} // namespace utils

} // namespace sat_solver