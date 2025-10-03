# 3SATオラクル

３SAT問題のグロバーアルゴリズムのオラクルを生成するプラグラム

## Project Structure

```
3SAToracle/
├── src/                   	    # Python quantum circuit implementation
│   ├── cnf_to_mct_json.py	    # CNFからJSONフォーマット
│   └── quantum_circuit.schema.json # JSONフォーマットのschema
├── external/                       # 外部からのコード
│   └── t-par                       # TカウントとTdepth削減(https://github.com/meamy/t-par)
├── lib/                            # TBD
├── test/                           # pytest
├── doc/                            # Documentation
├── CMakeLists.txt                  # Top-level build configuration
├── setup.sh                        # 初期セットアップスクリプト
└── README.md                       # 本ファイル
```

## Installation Guide

### Prerequisites

#### System Requirements
- **Python 3.8+**
- **CMake 3.12+**
- **C++17 compatible compiler** (GCC 7+, Clang 7+, MSVC 2019+)
- **Git** (for cloning the repository)

#### Operating System Support
- Linux (Ubuntu 18.04+, CentOS 7+)
- macOS (10.14+)
- Windows (with Visual Studio 2019+ or MinGW)

### Step 1: レポジトリーをクローヌ

```bash
git clone https://github.com/ritsu-NGC/3SAToracle.git
cd 3SAToracle
chmod +x setup.sh
./setup.sh
```

### Step 2: Install Python Dependencies

```bash
# Install core dependencies
pip install qiskit qiskit-aer numpy pytest pybind11

# Install optional dependencies for advanced features
pip install mqt.qcec  # For quantum circuit equivalence checking
```

### Step 3: Verify Installation

```bash
cd src
python cnf_to_mct_json.py --random --k=3 --nclauses=10 --nvars=10
```

### Step 5: pytest実行　

```bash
# 全テスト実行
pytest test/ -v
```

## Usage
```bash
usage: cnf_to_mct_json.py [-h] [--random] [--nvars NVARS] [--nclauses NCLAUSES] [--k K] [--seed SEED] [--cnf CNF] [--json JSON]
                          [--json_decomp JSON_DECOMP] [--ascii ASCII] [--ascii_decomp ASCII_DECOMP] [--quantikz QUANTIKZ]
                          [--quantikz_decomp QUANTIKZ_DECOMP]

Generate random CNF, build quantum circuit, and output JSON and diagrams.

options:
  -h, --help            show this help message and exit
  --random              Generate a random CNF file.
  --nvars NVARS         Number of variables for random CNF.
  --nclauses NCLAUSES   Number of clauses for random CNF.
  --k K                 Clause width for random CNF.
  --seed SEED           Random seed for CNF generation.
  --cnf CNF             Input/output CNF file.
  --json JSON           Output JSON file.
  --json_decomp JSON_DECOMP
                        Output decomposed JSON file.
  --ascii ASCII         ASCII diagram output file for original circuit.
  --ascii_decomp ASCII_DECOMP
                        ASCII diagram output file for decomposed circuit.
  --quantikz QUANTIKZ   Quantikz diagram output file for original circuit.
  --quantikz_decomp QUANTIKZ_DECOMP
                        Quantikz diagram output file for decomposed circuit.
```


## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run the test suite: `pytest test/ -v`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- **Grover's Algorithm**: L. K. Grover, "A fast quantum mechanical algorithm for database search," 1996
- **Qiskit**: Open-source quantum computing framework by IBM

## Acknowledgments

- IBM Qiskit team for the quantum computing framework
- pybind11 developers for C++/Python integration
- mqt.qcec team for quantum circuit equivalence checking tools