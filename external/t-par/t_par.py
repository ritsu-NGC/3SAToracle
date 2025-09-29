from qiskit import QuantumCircuit,QuantumRegister

from dd import cudd
from textwrap import dedent
from qiskit import transpile
import subprocess

#from src.circuit_to_logic import *
import logging
import os
import sys
import gc
#import memory-profiler
import random
import re

def write_qc_format(circuit: QuantumCircuit, filename: str):
    """Write a Qiskit QuantumCircuit to a .qc format file"""
    gate_map = {
        'cx': 'tof',
        'ccx': 'tof',
        'mcx': 'tof',        
        'x': 'X',
        'h': 'H',
        't': 'T',
        'tdg': 'T*',
        'z': 'Z',
        'y': 'Y',
        's': 'P',
        'sdg': 'P*',
        # Add more as neededA 
    }
    #os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        qubit_indices = [str(i) for i in range(circuit.num_qubits)]
        f.write(f".v {' '.join(qubit_indices)}\n")
        f.write(f".i {' '.join(qubit_indices)}\n")
        f.write(f".o {' '.join(qubit_indices)}\n")                
        f.write("\nBEGIN\n\n")
        for inst, qargs, cargs in circuit.data:
            name = inst.name.lower()
            if name in gate_map:
                gate_label = gate_map[name]
                qubits = [circuit.find_bit(q).index for q in qargs]
                f.write(f"{gate_label} {' '.join(map(str, qubits))}\n")
            # else:
            #     print(f"Warning: Gate {name} not supported in .qc format")
        f.write(f"\nEND")

def read_qc_format(filename):
    """Read a .qc file (as written by write_qc_format) and reconstruct a Qiskit QuantumCircuit."""
    # Reverse map from .qc labels to Qiskit gate names
    reverse_gate_map = {
        'tof': lambda qc, qs: qc.ccx(*qs) if len(qs) == 3 else qc.mcx(*qs) if len(qs) > 3 else qc.cx(*qs),
        'X':   lambda qc, qs: qc.x(*qs),
        'H':   lambda qc, qs: qc.h(*qs),
        'T':   lambda qc, qs: qc.t(*qs),
        'T*':  lambda qc, qs: qc.tdg(*qs),
        'Z':   lambda qc, qs: qc.z(*qs),
        'Y':   lambda qc, qs: qc.y(*qs),
        'P':   lambda qc, qs: qc.s(*qs),
        'P*':  lambda qc, qs: qc.sdg(*qs),
        # Extend if more gates are supported
    }

    with open(filename, 'r') as f:
        lines = f.readlines()

    qubits_declared = False
    num_qubits = 0
    circuit = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('.'):
            # Parse number of qubits from ".v" or ".i" line
            if line.startswith('.v') or line.startswith('.i'):
                qlist = line.split()[1:]
                num_qubits = len(qlist)
            continue
        if line == "BEGIN":
            qubits_declared = True
            if num_qubits == 0:
                raise ValueError("No qubit declaration found in .qc file before BEGIN")
            circuit = QuantumCircuit(num_qubits)
            continue
        if line == "END":
            break
        if qubits_declared:
            tokens = line.split()
            if not tokens:
                continue
            gate_label = tokens[0]
            qubit_indices = [int(q) for q in tokens[1:]]
            if gate_label not in reverse_gate_map:
                raise ValueError(f"Unsupported gate label {gate_label} in .qc file")
            # Apply the gate using the mapping
            reverse_gate_map[gate_label](circuit, qubit_indices)

    if circuit is None:
        raise ValueError("No circuit found in file (missing BEGIN/END?)")
    return circuit

def run_tpar(qc):
    filename  = "circ"
    circ_name = filename + ".qc"
    write_qc_format(qc,circ_name)
    with open(filename + ".log","w") as logfile, open(filename + ".qc","r") as infile:
        result = subprocess.run(["../external/t-par/t-par"], stdin=infile, stdout=logfile,capture_output=False, text=True)
    return read_qc_format("circ.log")
