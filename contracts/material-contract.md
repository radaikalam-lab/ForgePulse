# Material Contract

## Purpose

Define the semantics of material results and material state produced by FJH experiments, without inventing unsupported physical properties.

## Terminology

- **MaterialResult**: The experimental output material, including yield and characterization.
- **MaterialState**: The condition of a material at a point in time.
- **CharacterizationResult**: Structured characterization data.
- **YieldRepresentation**: A yield value with explicit basis and provenance.

## Invariants

1. Material properties are represented, not claimed as physical truth.
2. Unknown values remain unknown; no values are manufactured for unmeasured properties.
3. Every yield representation includes explicit basis and calculation method.
4. Material state preserves provenance to source experiments and measurements.

## Yield Basis

Possible yield bases include:

- `mass_basis`
- `molar_basis`
- `elemental_basis`
- `energy_basis`
- `process_basis`

The basis must be explicit; `yield = final_mass / initial_mass` is not assumed unless the experiment defines it.

## Material State Dimensions

Potential dimensions (all optional):

- `composition`
- `structure`
- `morphology`
- `electronic_properties`
- `thermal_properties`
- `optical_properties`
- `mechanical_properties`
- `provenance`

## Serialization

- UTF-8 JSON
- Sorted keys
- Explicit units
- UTC timestamps
- No NaN or Infinity
- Null values represented explicitly as `null`

## Failure Semantics

- `ProvenanceError`: lineage from source experiment or measurement is missing.

## Authority Boundary

- Material results are derived from measurements.
- Characterization is performed by instruments or analysis pipelines.
- ForgePulse does not claim physical validity of material properties.

## Examples

```json
{
  "material_result_id": "mat-001",
  "experiment_id": "exp-001",
  "yield": {
    "value": 0.35,
    "unit": "g/g",
    "basis": "mass_basis",
    "calculation_method": "final_mass / initial_mass",
    "input_references": ["meas-001", "meas-002"]
  },
  "material_state": {
    "composition": {
      "carbon": { "value": 0.92, "unit": "mass_fraction" },
      "hydrogen": null
    },
    "structure": null
  }
}
```

## Non-Goals

- This contract does not define universal material property ontologies.
- This contract does not enforce specific characterization methods.
