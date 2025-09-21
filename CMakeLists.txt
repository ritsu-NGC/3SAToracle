cmake_minimum_required(VERSION 3.12)
project(3SATOracle VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Add the lib subdirectory first
add_subdirectory(lib)

# Create a custom target to build Python modules
add_custom_target(python_modules ALL
    DEPENDS sat_solver_py
    COMMENT "Building Python modules"
)

# Create a custom target to copy Python modules to src directory
add_custom_command(
    TARGET python_modules POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:sat_solver_py>
        ${CMAKE_SOURCE_DIR}/src/
    COMMENT "Copying Python module to src directory"
)

# Create installation target
install(TARGETS sat_solver_py
    LIBRARY DESTINATION ${CMAKE_SOURCE_DIR}/src
)

# Add a custom target for testing
add_custom_target(run_tests
    COMMAND ${Python_EXECUTABLE} -m pytest ${CMAKE_SOURCE_DIR}/test/ -v
    DEPENDS python_modules
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Running Python tests"
)

# Add a target to install Python dependencies
add_custom_target(install_python_deps
    COMMAND ${Python_EXECUTABLE} -m pip install qiskit pytest pybind11 mqt.qcec numpy
    COMMENT "Installing Python dependencies"
)

# Print configuration information
message(STATUS "Python executable: ${Python_EXECUTABLE}")
message(STATUS "Python include dirs: ${Python_INCLUDE_DIRS}")
message(STATUS "Python libraries: ${Python_LIBRARIES}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# Set default build type to Release if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build" FORCE)
endif()

# Add compiler flags for better optimization and debugging
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -O0 -Wall -Wextra")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -DNDEBUG")
endif()

# Create a configuration summary
message(STATUS "")
message(STATUS "3SAT Oracle Configuration Summary:")
message(STATUS "  Project: ${PROJECT_NAME}")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Source directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "  Binary directory: ${CMAKE_BINARY_DIR}")
message(STATUS "")