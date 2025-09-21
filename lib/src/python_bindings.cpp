#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "sat_solver.h"

namespace py = pybind11;

PYBIND11_MODULE(sat_solver, m) {
    m.doc() = "SAT Solver C++ Library with Python Bindings";
    
    // Bind the SATSolver class
    py::class_<sat_solver::SATSolver>(m, "SATSolver")
        .def(py::init<>())
        .def("add_clause", &sat_solver::SATSolver::add_clause,
             "Add a clause to the SAT formula",
             py::arg("clause"))
        .def("clear", &sat_solver::SATSolver::clear,
             "Clear all clauses from the formula")
        .def("get_num_variables", &sat_solver::SATSolver::get_num_variables,
             "Get the number of variables in the formula")
        .def("get_num_clauses", &sat_solver::SATSolver::get_num_clauses,
             "Get the number of clauses in the formula")
        .def("is_satisfiable", &sat_solver::SATSolver::is_satisfiable,
             "Check if the current formula is satisfiable")
        .def("get_satisfying_assignment", &sat_solver::SATSolver::get_satisfying_assignment,
             "Get a satisfying assignment if one exists")
        .def("to_string", &sat_solver::SATSolver::to_string,
             "Convert the formula to a string representation")
        .def("is_3sat", &sat_solver::SATSolver::is_3sat,
             "Validate that all clauses are 3-SAT clauses")
        .def("__repr__", [](const sat_solver::SATSolver& solver) {
            return "<SATSolver with " + std::to_string(solver.get_num_clauses()) + 
                   " clauses and " + std::to_string(solver.get_num_variables()) + " variables>";
        });
    
    // Bind utility functions
    py::module_ utils = m.def_submodule("utils", "Utility functions for SAT manipulation");
    
    utils.def("generate_random_3sat", &sat_solver::utils::generate_random_3sat,
              "Generate a random 3-SAT formula",
              py::arg("num_vars"), py::arg("num_clauses"));
              
    utils.def("are_equivalent", &sat_solver::utils::are_equivalent,
              "Check if two formulas are equivalent",
              py::arg("f1"), py::arg("f2"));
    
    // Add some convenience functions
    m.def("create_solver_from_clauses", [](const std::vector<std::vector<int>>& clauses) {
        auto solver = sat_solver::SATSolver();
        for (const auto& clause : clauses) {
            solver.add_clause(clause);
        }
        return solver;
    }, "Create a SAT solver from a list of clauses");
    
    // Version info
    m.attr("__version__") = "1.0.0";
}