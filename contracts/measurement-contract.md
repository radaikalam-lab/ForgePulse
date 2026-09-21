# Measurement Contract

## Purpose

Define the semantics of raw, derived, and interpreted measurements, preserving explicit distinctions and lineage.

## Terminology

- **RawMeasurement**: An observation directly acquired from an instrument or simulator.
- **DerivedMeasurement**: A quantity computed from one or more raw or derived measurements.
- **InterpretedResult**: A scientific interpretation of measurements, explicitly marked as interpretation.
- **MeasurementSeries**: A structured time-series or vector measurement.
- **ElectricalObservation**: Electrical domain measurement.
- **ThermalObservation**: Thermal domain measurement.
- **PulseObservation**: Combined pulse-domain observation.

## Invariants

1. Raw measurements are never silently replaced by derived or interpreted values.
2. Every derived measurement preserves lineage to its source data.
3. Simulated observations are explicitly identified as simulated.
4. Physical measurements are never indistinguishable from simulated data.
5. Every measurement has an explicit unit.

## Identity

```text
measurement_id: str
quantity: str
source_type: str  # "raw" | "derived" | "interpreted" | "simulated"
provenance: ProvenanceReference
```

## Measurement Series

```text
measurement_id: str
quantity: str
values: list[float] | list[list[float]]
unit: str
sampling_rate: Quantity
start_time: datetime (UTC)
timestamps: list[datetime] | null
instrument_reference: str | null
provenance: ProvenanceReference
```

## Serialization

- UTF-8 JSON
- Sorted keys
- Explicit units
- UTC timestamps
- No NaN or Infinity

## Failure Semantics

- `MeasurementValidationError`: measurement fails structural or semantic validation.
- `ProvenanceError`: lineage cannot be established.

## Authority Boundary

- Measurements are acquired by instruments or simulators.
- Derivation is performed by ForgePulse.
- Interpretation is explicitly labeled and never promoted to measurement.

## Examples

```json
{
  "measurement_id": "meas-001",
  "quantity": "voltage",
  "source_type": "raw",
  "unit": "V",
  "values": [118.5, 119.2, 118.9],
  "sampling_rate": { "value": 1000.0, "unit": "Hz" },
  "start_time": "2026-01-15T10:30:05Z",
  "instrument_reference": "daq-01",
  "provenance": {
    "execution_id": "exec-001",
    "measurement_id": "meas-001"
  }
}
```

## Non-Goals

- This contract does not define vendor-specific DAQ protocols.
- This contract does not define hardware calibration procedures.
