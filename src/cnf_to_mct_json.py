import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import MCXGate
from qiskit import qasm2

import json
import random
import argparse
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'external', 't-par')))
from t_par import run_tpar

def generate_random_cnf(nvars, nclauses, k=3, seed=None):
    if seed is not None:
        random.seed(seed)
    clauses = []
    for _ in range(nclauses):
        clause_vars = random.sample(range(1, nvars + 1), k)
        clause = [v if random.choice([True, False]) else -v for v in clause_vars]
        clauses.append(clause)
    return clauses

def write_dimacs_cnf(nvars, clauses, path):
    with open(path, 'w') as f:
        f.write(f"p cnf {nvars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(str(lit) for lit in clause) + " 0\n")

def read_dimacs_cnf(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    nvars = 0
    clauses = []
    for line in lines:
        if line.startswith('c') or line.strip() == '':
            continue
        if line.startswith('p cnf'):
            nvars = int(line.split()[2])
            continue
        clause = [int(x) for x in line.strip().split() if x != '0']
        if clause:
            clauses.append(clause)
    return nvars, clauses

def build_circuit_from_cnf_with_global_and(nvars, clauses):
    n_clauses = len(clauses)
    n_ancilla = max(0, max(len(c) - 2 for c in clauses)) if clauses else 0
    num_qubits = nvars + n_clauses + n_ancilla + 1  # +1 for global output qubit
    qc = QuantumCircuit(num_qubits, 1)  # measure only global output

    var_qubits = [i for i in range(nvars)]
    clause_qubits = [nvars + i for i in range(n_clauses)]
    ancilla_qubits = [nvars + n_clauses + i for i in range(n_ancilla)]
    global_qubit = nvars + n_clauses + n_ancilla

    for q in clause_qubits:
        qc.x(q)

    clause_gate_history = []
    for i, clause in enumerate(clauses):
        controls = []
        control_flips = []
        for lit in clause:
            idx = abs(lit) - 1
            controls.append(var_qubits[idx])
            control_flips.append(0 if lit > 0 else 1)
        target = clause_qubits[i]
        for ctrl, flip in zip(controls, control_flips):
            if flip:
                qc.x(ctrl)
        if len(controls) == 1:
            qc.cx(controls[0], target)
            clause_gate_history.append(('cx', controls[0], target, control_flips.copy()))
        elif len(controls) == 2:
            qc.ccx(controls[0], controls[1], target)
            clause_gate_history.append(('ccx', controls[:2], target, control_flips.copy()))
        else:
            gate = MCXGate(len(controls))
            qc.append(gate, controls + [target])
            clause_gate_history.append(('mcx', controls.copy(), target, control_flips.copy()))
        for ctrl, flip in zip(controls, control_flips):
            if flip:
                qc.x(ctrl)

    if n_clauses == 1:
        qc.cx(clause_qubits[0], global_qubit)
    elif n_clauses == 2:
        qc.ccx(clause_qubits[0], clause_qubits[1], global_qubit)
    elif n_clauses > 2:
        gate = MCXGate(n_clauses)
        qc.append(gate, clause_qubits + [global_qubit])

    for i in reversed(range(len(clause_gate_history))):
        entry = clause_gate_history[i]
        if entry[0] == 'cx':
            ctrl, target, control_flips = entry[1], entry[2], entry[3]
            for flip in control_flips:
                if flip:
                    qc.x(ctrl)
            qc.cx(ctrl, target)
            for flip in control_flips:
                if flip:
                    qc.x(ctrl)
        elif entry[0] == 'ccx':
            ctrls, target, control_flips = entry[1], entry[2], entry[3]
            for ctrl, flip in zip(ctrls, control_flips):
                if flip:
                    qc.x(ctrl)
            qc.ccx(ctrls[0], ctrls[1], target)
            for ctrl, flip in zip(ctrls, control_flips):
                if flip:
                    qc.x(ctrl)
        elif entry[0] == 'mcx':
            controls, target, control_flips = entry[1], entry[2], entry[3]
            for ctrl, flip in zip(controls, control_flips):
                if flip:
                    qc.x(ctrl)
            gate = MCXGate(len(controls))
            qc.append(gate, controls + [target])
            for ctrl, flip in zip(controls, control_flips):
                if flip:
                    qc.x(ctrl)

    return qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit

def build_clifford_t_decomposition_circuit(qc):
    # Decompose using the specified basis gates
    # h, cx, s, sdg, t, tdg, z
    basis_gates = ['h', 'cx', 's', 'sdg', 't', 'tdg', 'z']
    decomposed_qc = transpile(qc, basis_gates=basis_gates, optimization_level=0)
    return decomposed_qc

def circuit_to_json(qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit):
    qmap = {}
    all_qs = var_qubits + clause_qubits + ancilla_qubits + [global_qubit]
    for i, q in enumerate(all_qs):
        qmap[q] = f"Q{i}"

    json_gates = []
    for inst, qargs, cargs in qc.data:
        name = inst.name.upper()
        targets = [qmap[q._index] for q in qargs[-1:]]
        controls = [qmap[q._index] for q in qargs[:-1]]
        gate_json = {
            "name": name if name != "MCX" else "CCX" if len(controls) == 2 else "MCX",
            "targets": targets
        }
        if controls:
            gate_json["controls"] = controls
        json_gates.append(gate_json)
    return json_gates

def write_circuit_ascii(qc, filename):
    # Save ASCII diagram to file
    ascii_diagram = qc.draw(output='text')
    with open(filename, 'w') as f:
        f.write(str(ascii_diagram))

def write_circuit_quantikz(qc, filename):
    # Save quantikz latex diagram to file
    try:
        quantikz_latex = qc.draw(output='latex_source')
    except Exception as e:
        quantikz_latex = f"Error generating quantikz diagram: {e}"
    with open(filename, 'w') as f:
        f.write(str(quantikz_latex))

def opt_circ(qc):
    with open("circ.qasm",'w') as f:
        f.write(qasm2.dumps(qc))
    return run_tpar(qc)

    
def main():
    parser = argparse.ArgumentParser(description="Generate random CNF, build quantum circuit, and output JSON and diagrams.")
    parser.add_argument('--random', action='store_true', help="Generate a random CNF file.")
    parser.add_argument('--nvars', type=int, default=45, help="Number of variables for random CNF.")
    parser.add_argument('--nclauses', type=int, default=140, help="Number of clauses for random CNF.")
    parser.add_argument('--k', type=int, default=3, help="Clause width for random CNF.")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for CNF generation.")
    parser.add_argument('--cnf', type=str, default="random.cnf", help="Input/output CNF file.")
    parser.add_argument('--json', type=str, default="output.json", help="Output JSON file.")
    parser.add_argument('--json_decomp', type=str, default="output_decomp.json", help="Output decomposed JSON file.")
    parser.add_argument('--ascii', type=str, default="circuit_ascii.txt", help="ASCII diagram output file for original circuit.")
    parser.add_argument('--ascii_decomp', type=str, default="circuit_ascii_decomp.txt", help="ASCII diagram output file for decomposed circuit.")
    parser.add_argument('--quantikz', type=str, default="circuit_quantikz.tex", help="Quantikz diagram output file for original circuit.")
    parser.add_argument('--quantikz_decomp', type=str, default="circuit_quantikz_decomp.tex", help="Quantikz diagram output file for decomposed circuit.")
    args = parser.parse_args()

    if args.random or not (args.cnf and os.path.exists(args.cnf)):
        clauses = generate_random_cnf(args.nvars, args.nclauses, k=args.k, seed=args.seed)
        write_dimacs_cnf(args.nvars, clauses, args.cnf)
        print(f"Random CNF written to {args.cnf}:")
        with open(args.cnf) as f:
            print(f.read())
        nvars = args.nvars
    else:
        nvars, clauses = read_dimacs_cnf(args.cnf)

    qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit = build_circuit_from_cnf_with_global_and(nvars, clauses)

    json_gates = circuit_to_json(qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit)
    with open(args.json, 'w') as f:
        json.dump(json_gates, f, indent=2, ensure_ascii=False)
    print(f"Quantum circuit JSON written to {args.json}")
    print(f"Global output qubit index: {global_qubit}")

    write_circuit_ascii(qc, args.ascii)
    print(f"ASCII diagram written to {args.ascii}")
    write_circuit_quantikz(qc, args.quantikz)
    print(f"Quantikz diagram written to {args.quantikz}")

    decomposed_qc = build_clifford_t_decomposition_circuit(qc)
    decomposed_qc = opt_circ(decomposed_qc)    
    json_gates_decomp = circuit_to_json(decomposed_qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit)
    with open(args.json_decomp, 'w') as f:
        json.dump(json_gates_decomp, f, indent=2, ensure_ascii=False)
    print(f"Decomposed Clifford+T circuit JSON written to {args.json_decomp}")

    write_circuit_ascii(decomposed_qc, args.ascii_decomp)
    print(f"ASCII diagram (decomposed) written to {args.ascii_decomp}")
    write_circuit_quantikz(decomposed_qc, args.quantikz_decomp)
    print(f"Quantikz diagram (decomposed) written to {args.quantikz_decomp}")

if __name__ == "__main__":
    main()
