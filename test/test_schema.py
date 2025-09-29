import json
import pytest
import jsonschema

# Path to your schema file
SCHEMA_PATH = "../src/quantum_circuit.schema.json"

@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_json_against_schema(json_path, schema):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    jsonschema.validate(instance=data, schema=schema)

def test_example_quantum_circuit_valid(schema):
    # Path to your example JSON file to validate
    json_path = "example_quantum_circuit.json"
    validate_json_against_schema(json_path, schema)

@pytest.mark.parametrize("invalid_json_path", [
    "invalid_quantum_circuit_missing_targets.json",
    "invalid_quantum_circuit_bad_control_flips.json"
])
def test_invalid_quantum_circuit(invalid_json_path, schema):
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_json_against_schema(invalid_json_path, schema)
