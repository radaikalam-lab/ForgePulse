# ForgePulse Glossary

## A

**Additive**: A material added to the feedstock in an FJH experiment.

**ActualProcess**: The electrical and thermal parameters measured during physical execution. Contrast with `TargetProcess`.

**Advisory**: A response from Cognitia to a ForgePulse request.

**Assumption**: An explicit premise of an interpretation or evidence item.

## C

**Chamber**: The reaction vessel configuration for an experiment.

**CharacterizationResult**: Structured post-experiment characterization data.

**CharacterizationRequirement**: A requirement for post-process material characterization.

**Cognitia**: An external cognitive infrastructure dependency. Advisory only; has no execution or safety authority over ForgePulse.

**CompetingInterpretation**: Alternative explanation retained explicitly when evidence does not distinguish between interpretations.

**ConstraintViolation**: A process constraint violated by an experiment specification.

## D

**DerivedMeasurement**: A quantity computed from one or more raw or derived measurements. Lineage to source data is preserved.

## E

**EdgeIntegrationBoundary**: Manages the authority boundary between ForgePulse domain and external systems. Enforces state-dependent access controls.

**ElectricalObservation**: An electrical domain measurement (voltage, current, resistance, etc.).

**ElectricalCharacterization**: Structured electrical characterization derived from measurements (peak voltage, peak current, average power, pulse energy).

**Evidence**: Information supporting or constraining an interpretation.

**Experiment**: A complete, versioned scientific procedure definition with lifecycle state.

**ExperimentObjective**: The scientific goal of an experiment.

**ExperimentProposal**: An initial experiment specification before validation.

**ExperimentProvenance**: Structured lineage for an experiment and its derived artifacts.

**ExperimentVersion**: An immutable snapshot of an experiment at a specific lifecycle stage.

**Execution**: An attempt to run a `ValidatedExperimentSnapshot`.

**ExecutionStatus**: The current state of an execution (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `ABORTED`).

## F

**Feedstock**: The starting material for an FJH experiment.

**FJHController**: The entity responsible for physically executing pulses.

## H

**Hypothesis**: Candidate scientific explanation.

**HypothesisReference**: A reference to a hypothesis under evaluation.

## I

**InvalidExperiment**: Raised when an experiment specification is structurally or semantically invalid.

**InvalidPulseSequence**: Raised when a pulse sequence violates domain rules.

**InvalidTransition**: Raised when an invalid experiment lifecycle transition is attempted.

**Interpretation**: Explicit inference derived from available evidence. Distinct from measurement, characterization, and material truth.

**InterpretationResult**: Structured scientific interpretation.

**InterpretationStatus**: Lifecycle state of an interpretation (`PROPOSED`, `UNDER_REVIEW`, `SUPPORTED`, `REFUTED`, `UNRESOLVED`, `SUPERSEDED`).

**InterpretedResult**: A scientific interpretation of measurements, explicitly marked as interpretation. Never promoted to measurement.

## L

**LifecycleEvent**: A record of a state transition in the experiment lifecycle.

**LineageReference**: A reference to another artifact by its stable identifier.

## M

**MaterialEvolution**: Candidate material state proposed from interpretation. Does not silently become canonical truth.

**MaterialResult**: The experimental output material, including yield and characterization.

**MaterialState**: The condition of a material at a point in time. Unknown values remain unknown.

**MeasurementProvenanceError**: Raised when lineage cannot be established.

**MeasurementRequirement**: What must be measured during execution.

**MeasurementIngestionBoundary**: Provider-neutral interface for ingesting normalized measurement representations into ForgePulse. Does not control instruments.

**MeasurementPipeline**: Stages for processing measurements from raw through derived to characterization.

**MeasurementSeries**: A structured time-series or vector measurement. `sampling_rate` is optional when explicit `timestamps` are provided.

**MeasurementTranslator**: Translates raw edge data into normalized ForgePulse measurements.

**MeasurementValidationError**: Raised when a measurement fails structural or semantic validation.

## P

**ProcessConstraint**: Validity rules for the experiment specification. Not physical safety interlocks.

**Provenance**: The lineage of an artifact from its source data through all transformations.

**ProvenanceError**: Raised when required lineage is missing or circular.

**ProvenanceRecord**: A structured record of lineage.

**Pulse**: A single electrical pulse specification.

**PulseObservation**: A combined pulse-domain observation.

**PulseStatistics**: Deterministic pulse-level statistics derived from voltage and current series.

**PulseSequence**: An ordered set of pulses.

## Q

**Quantity**: A physical value with an explicit unit.

## R

**RawMeasurement**: An observation directly acquired from an instrument or simulator. Never replaced by derived values.

**Residual**: Observed information not adequately explained by the current interpretation. Not error, not failure, not noise unless explicitly established.

## S

**SafetyInterlock**: Physical safety systems independent of ForgePulse process constraints.

**SimulatedObservation**: An observation produced by the simulator, explicitly marked as simulated.

**SimulationMetadata**: Metadata identifying the simulator implementation, model version, seed, sampling rate, and documented assumptions.

**Simulator**: A deterministic program that produces synthetic FJH observations from a validated experiment snapshot.

**SimulatorResult**: The complete output of a simulation run, including measurements, observations, metadata, and provenance.

**SnapshotViolation**: An attempt to mutate an immutable snapshot.

**SnapshotValidator**: Creates immutable validated experiment snapshots from experiment specifications. Validates first, then snapshots only valid specifications.

**SourceType**: Enumeration distinguishing raw, derived, interpreted, simulated, and measured data.

**SyntheticEdgeSource**: Generates deterministic synthetic measurement data for testing and simulation.

## T

**TargetProcess**: The electrical and thermal parameters requested for the experiment. Contrast with `ActualProcess`.

**ThermalObservation**: A thermal domain measurement (temperature, heat flux, etc.).

**ThermalCharacterization**: Structured thermal characterization derived from temperature measurements (peak temperature, temperature rise, heating/cooling rates).

## U

**Uncertainty**: Measurement uncertainty representation, distinct from epistemic confidence.

**Unknown**: Information not established by available evidence. First-class; not represented as null, 0, false, or low confidence.

**UnsupportedOperation**: Raised when an operation is not supported in the current context.

## V

**ValidatedExperimentSnapshot**: An immutable validated specification ready for execution.

**ValidationResult**: The outcome of validating an experiment specification.

**Validator**: The entity or process performing validation.
