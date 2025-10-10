import qiskit
from qiskit import QuantumCircuit, transpile, QuantumRegister
from qiskit.circuit.library import MCXGate
from qiskit.synthesis import synth_mcx_1_clean_kg24
from qiskit import qasm2

import json
import random
import argparse
import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'external', 't-par')))
from t_par import run_tpar

# SAT solver dependencies
try:
    from pysat.solvers import Solver
except ImportError:
    Solver = None

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

def run_sat_solver_on_dimacs(path):
    if Solver is None:
        print("PySAT is not installed. Please run 'pip install python-sat'")
        return ""
    print(f"Running SAT solver on {path} ...")
    # Parse DIMACS and add clauses
    clauses = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("c") or line.startswith("p"):
                continue
            clause = [int(lit) for lit in line.split() if lit != '0']
            if clause:
                clauses.append(clause)
    start = time.time()
    with Solver(name='g3', bootstrap_with=clauses) as solver:
        sat = solver.solve()
        elapsed = time.time() - start
        if sat:
            status_str = "SATISFIABLE"
            model = solver.get_model()
            result_comment = (
                f"c SAT solver result: {status_str}\n"
                f"c SAT time: {elapsed:.6f} seconds\n"
                f"c SAT solution (first): {' '.join(str(lit) for lit in model)}\n"
            )
        else:
            status_str = "UNSATISFIABLE"
            result_comment = (
                f"c SAT solver result: {status_str}\n"
                f"c SAT time: {elapsed:.6f} seconds\n"
            )
        print(result_comment)

    return result_comment

def run_naive_sat_solver_on_dimacs(path):
    import random
    # Parse DIMACS and add clauses
    clauses = []
    nvars = 0
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("c"):
                continue
            if line.startswith("p cnf"):
                nvars = int(line.split()[2])
                continue
            clause = [int(lit) for lit in line.split() if lit != '0']
            if clause:
                clauses.append(clause)
    if nvars == 0 or not clauses:
        print("Naive SAT: No variables or clauses found.")
        return ""

    print(f"Running naive SAT timing estimate on {path} (nvars={nvars}) ...")

    # Try a single random assignment (could also use all 0s for deterministic)
    assignment = [random.choice([False, True]) for _ in range(nvars)]

    # Measure the time to check one assignment
    start = time.time()
    satisfied = True
    for clause in clauses:
        clause_satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            var_val = assignment[var_idx]
            if (lit > 0 and var_val) or (lit < 0 and not var_val):
                clause_satisfied = True
                break
        if not clause_satisfied:
            satisfied = False
            break
    elapsed_one = time.time() - start

    total_assignments = 2 ** nvars
    worst_case_time = elapsed_one * total_assignments
    average_case_time = elapsed_one * (total_assignments / 2)

    result_comment = (
        f"c NAIVE SAT timing estimate (single assignment): {elapsed_one:.8f} seconds\n"
        f"c NAIVE SAT estimated worst-case time (all {total_assignments} assignments): {worst_case_time:.6f} seconds\n"
        f"c NAIVE SAT estimated average-case time (half assignments): {average_case_time:.6f} seconds\n"
    )
    print(result_comment)
    return result_comment

def prepend_comments_to_dimacs(path, comments):
    # Read original file
    with open(path, "r") as f:
        orig = f.read()
    # Write comments + orig
    with open(path, "w") as f:
        f.write(''.join(comments) + orig)

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

def decompose_mcx_clean(circ: QuantumCircuit,
                        synth_fn=synth_mcx_1_clean_kg24,
                        ancilla_prefix: str = "anc") -> QuantumCircuit:
    new_circ = QuantumCircuit(circ.num_qubits, circ.num_clbits)
    orig_qubit_map = {q: new_circ.qubits[i] for i, q in enumerate(circ.qubits)}
    orig_clbit_map = {c: new_circ.clbits[i] for i, c in enumerate(circ.clbits)}
    anc_counter = 0
    for instr, qargs, cargs in circ.data:
        if isinstance(instr, MCXGate):
            k = instr.num_ctrl_qubits
            sub = synth_fn(k)
            sub_nq = sub.num_qubits
            mapped_orig = [orig_qubit_map[q] for q in qargs]
            if len(mapped_orig) < sub_nq:
                missing = sub_nq - len(mapped_orig)
                old_nq = new_circ.num_qubits
                anc_name = f"{ancilla_prefix}{anc_counter}"
                anc_counter += 1
                anc_reg = QuantumRegister(missing, name=anc_name)
                new_circ.add_register(anc_reg)
                new_ancillas = new_circ.qubits[old_nq: old_nq + missing]
                if len(mapped_orig) >= 1:
                    controls = mapped_orig[:-1]
                    target = [mapped_orig[-1]]
                else:
                    controls = mapped_orig
                    target = []
                mapped_for_sub = controls + list(new_ancillas) + target
            else:
                mapped_for_sub = mapped_orig[:sub_nq]
            if len(mapped_for_sub) != sub_nq:
                raise RuntimeError(
                    f"mapped qubit count ({len(mapped_for_sub)}) != subcircuit qubits ({sub_nq})."
                )
            new_circ.compose(sub, qubits=mapped_for_sub, inplace=True)
        else:
            new_qargs = [orig_qubit_map[q] for q in qargs]
            new_cargs = [orig_clbit_map[c] for c in cargs]
            new_circ.append(instr, new_qargs, new_cargs)
    return new_circ

def build_clifford_t_decomposition_circuit(qc):
    decomposed_qc = decompose_mcx_clean(qc)
    with open('circ_anc.txt', 'w') as f:
        f.write(str(decomposed_qc.draw(output='text')))
    basis_gates = ['h', 'cx', 's', 'sdg', 't', 'tdg', 'z']
    decomposed_qc = transpile(decomposed_qc, basis_gates=basis_gates, optimization_level=0)

    # Map old qubits to new
    final_qc = QuantumCircuit(decomposed_qc.num_qubits, decomposed_qc.num_clbits)
    qubit_map = {q: final_qc.qubits[i] for i, q in enumerate(decomposed_qc.qubits)}
    clbit_map = {c: final_qc.clbits[i] for i, c in enumerate(decomposed_qc.clbits)}

    for inst, qargs, cargs in decomposed_qc.data:
        # Map qargs and cargs to this circuit's bits
        mapped_qargs = [qubit_map[q] for q in qargs]
        mapped_cargs = [clbit_map[c] for c in cargs]
        if inst.name == "s":
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
        elif inst.name == "sdg":
            final_qc.tdg(mapped_qargs[0])
            final_qc.tdg(mapped_qargs[0])
        elif inst.name == "z":
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
        else:
            final_qc.append(inst, mapped_qargs, mapped_cargs)

    return final_qc

def circuit_to_json(qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit):
    qmap = {}
    all_qs = qc.qubits
    for i, q in enumerate(all_qs):
        qmap[q] = f"Q{i}"
    json_gates = []
    for inst, qargs, cargs in qc.data:
        name = inst.name.upper()
        targets = [qmap[q] for q in qargs[-1:]]
        controls = [qmap[q] for q in qargs[:-1]]
        gate_json = {
            "name": name if name != "MCX" else "CCX" if len(controls) == 2 else "MCX",
            "targets": targets
        }
        if controls:
            gate_json["controls"] = controls
        json_gates.append(gate_json)
    return json_gates

def write_circuit_ascii(qc, filename):
    ascii_diagram = qc.draw(output='text')
    with open(filename, 'w') as f:
        f.write(str(ascii_diagram))

def write_circuit_quantikz(qc, filename):
    try:
        quantikz_latex = qc.draw(output='latex_source')
    except Exception as e:
        quantikz_latex = f"Error generating quantikz diagram: {e}"
    with open(filename, 'w') as f:
        f.write(str(quantikz_latex))

def opt_circ(qc):
    with open("circ.qasm",'w') as f:
        f.write(qasm2.dumps(qc))
    opt_qc = run_tpar(qc)
    qubit_map = {q: opt_qc.qubits[i] for i, q in enumerate(opt_qc.qubits)}
    clbit_map = {c: opt_qc.clbits[i] for i, c in enumerate(opt_qc.clbits)}
    final_qc = QuantumCircuit(opt_qc.num_qubits, opt_qc.num_clbits)
    for inst, qargs, cargs in opt_qc.data:
        # Map qargs and cargs to this circuit's bits
        mapped_qargs = [qubit_map[q] for q in qargs]
        mapped_cargs = [clbit_map[c] for c in cargs]
        if inst.name == "s":
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
        elif inst.name == "sdg":
            final_qc.tdg(mapped_qargs[0])
            final_qc.tdg(mapped_qargs[0])
        elif inst.name == "z":
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
            final_qc.t(mapped_qargs[0])
        else:
            final_qc.append(inst, mapped_qargs, mapped_cargs)
    return final_qc

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
    parser.add_argument('--sat', action='store_true', help="Run SAT solver on the CNF file after generation.")
    # Added for multiple configs
    parser.add_argument('--nconfigs', type=int, default=1, help="Number of random configurations to generate and run.")
    parser.add_argument('--nvars_min', type=int, default=None, help="Minimum number of variables (if varying).")
    parser.add_argument('--nvars_max', type=int, default=None, help="Maximum number of variables (if varying).")
    parser.add_argument('--nclauses_min', type=int, default=None, help="Minimum number of clauses (if varying).")
    parser.add_argument('--nclauses_max', type=int, default=None, help="Maximum number of clauses (if varying).")

    args = parser.parse_args()

    # If only one config, preserve previous behavior
    nconfigs = args.nconfigs if args.nconfigs > 0 else 1

    for i in range(nconfigs):
        # If random is set or --nconfigs > 1, always randomize
        if args.random or (nconfigs > 1):
            # Optionally randomize nvars/nclauses
            nvars = args.nvars
            nclauses = args.nclauses
            if args.nvars_min is not None and args.nvars_max is not None:
                nvars = random.randint(args.nvars_min, args.nvars_max)
            if args.nclauses_min is not None and args.nclauses_max is not None:
                nclauses = random.randint(args.nclauses_min, args.nclauses_max)
            # Different seed for each config unless overridden
            config_seed = args.seed + i if args.seed is not None else random.randint(0, 999999)

            # Unique file names for each configuration
            prefix = f"_config{i+1}"
            cnf_file = args.cnf.replace(".cnf", f"{prefix}.cnf")
            json_file = args.json.replace(".json", f"{prefix}.json")
            json_decomp_file = args.json_decomp.replace(".json", f"{prefix}.json")
            ascii_file = args.ascii.replace(".txt", f"{prefix}.txt")
            ascii_decomp_file = args.ascii_decomp.replace(".txt", f"{prefix}.txt")
            quantikz_file = args.quantikz.replace(".tex", f"{prefix}.tex")
            quantikz_decomp_file = args.quantikz_decomp.replace(".tex", f"{prefix}.tex")

            # Generate and write CNF
            clauses = generate_random_cnf(nvars, nclauses, k=args.k, seed=config_seed)
            write_dimacs_cnf(nvars, clauses, cnf_file)
            print(f"Random CNF written to {cnf_file} (nvars={nvars}, nclauses={nclauses}, seed={config_seed})")
            with open(cnf_file) as f:
                print(f.read())
        else:
            cnf_file = args.cnf
            json_file = args.json
            json_decomp_file = args.json_decomp
            ascii_file = args.ascii
            ascii_decomp_file = args.ascii_decomp
            quantikz_file = args.quantikz
            quantikz_decomp_file = args.quantikz_decomp
            nvars, clauses = read_dimacs_cnf(cnf_file)

        # Run SAT solvers if requested or if random generation occurred
        if args.sat or args.random or (nconfigs > 1):
            naive_result = run_naive_sat_solver_on_dimacs(cnf_file)
            pysat_result = run_sat_solver_on_dimacs(cnf_file)
            prepend_comments_to_dimacs(cnf_file, [naive_result, pysat_result])

        # Build and process quantum circuit
        qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit = build_circuit_from_cnf_with_global_and(nvars, clauses)
        json_gates = circuit_to_json(qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit)
        with open(json_file, 'w') as f:
            json.dump(json_gates, f, indent=2, ensure_ascii=False)
        print(f"Quantum circuit JSON written to {json_file}")
        print(f"Global output qubit index: {global_qubit}")

        write_circuit_ascii(qc, ascii_file)
        print(f"ASCII diagram written to {ascii_file}")
        write_circuit_quantikz(qc, quantikz_file)
        print(f"Quantikz diagram written to {quantikz_file}")

        decomposed_qc = build_clifford_t_decomposition_circuit(qc)
        new_decomposed_qc = opt_circ(decomposed_qc)
        json_gates_decomp = circuit_to_json(new_decomposed_qc, var_qubits, clause_qubits, ancilla_qubits, global_qubit)
        with open(json_decomp_file, 'w') as f:
            json.dump(json_gates_decomp, f, indent=2, ensure_ascii=False)
        print(f"Decomposed Clifford+T circuit JSON written to {json_decomp_file}")

        write_circuit_ascii(new_decomposed_qc, ascii_decomp_file)
        print(f"ASCII diagram (decomposed) written to {ascii_decomp_file}")
        write_circuit_quantikz(new_decomposed_qc, quantikz_decomp_file)
        print(f"Quantikz diagram (decomposed) written to {quantikz_decomp_file}")

if __name__ == "__main__":
    main()
