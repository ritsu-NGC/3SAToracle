cmake_minimum_required(VERSION 3.12)
project(SATSolver VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find pybind11
find_package(pybind11 QUIET)
if(NOT pybind11_FOUND)
    # If pybind11 is not found, try to find it via pip
    execute_process(
        COMMAND ${Python_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(pybind11_DIR)
        find_package(pybind11 REQUIRED PATHS ${pybind11_DIR})
    else()
        message(FATAL_ERROR "pybind11 not found. Please install it with: pip install pybind11")
    endif()
endif()

# Create the SAT solver library
add_library(sat_solver_lib STATIC
    src/sat_solver.cpp
)

target_include_directories(sat_solver_lib PUBLIC
    include
)

# Set position independent code for shared library compatibility
set_target_properties(sat_solver_lib PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

# Create Python bindings
pybind11_add_module(sat_solver_py
    src/python_bindings.cpp
)

target_link_libraries(sat_solver_py PRIVATE
    sat_solver_lib
)

target_include_directories(sat_solver_py PRIVATE
    include
)

# Set properties for the Python module
set_target_properties(sat_solver_py PROPERTIES
    OUTPUT_NAME "sat_solver"
    PREFIX ""
)

# Installation
install(TARGETS sat_solver_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include
)

install(TARGETS sat_solver_py
    LIBRARY DESTINATION python
)