"""
Clinical Health FHIR Observation Extraction Engine
Demonstrates deeply nested Pydantic schemas under OpenAI Strict Mode.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from openai import OpenAI

class Coding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: str = Field(description="Coding system URI, e.g., 'http://loinc.org' or 'http://snomed.info/sct'")
    code: str = Field(description="Standardized alphanumeric clinical code, e.g., '8867-4' for Heart Rate")
    display: str = Field(description="Human-readable concept name, e.g., 'Heart rate'")

class CodeableConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding: List[Coding] = Field(description="List of standardized codings representing the concept")
    text: str = Field(description="Original verbatim clinical terminology recorded by practitioner")

class Quantity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float = Field(description="Numerical measurement value")
    unit: str = Field(description="Clinical unit of measurement, e.g., 'mm[Hg]', 'beats/min'")
    system: str = Field(default="http://unitsofmeasure.org", description="UCUM measurement system URI")
    code: str = Field(description="Standard UCUM unit code")

class FHIRObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resourceType: Literal["Observation"] = "Observation"
    status: Literal["registered", "preliminary", "final", "amended"] = "final"
    code: CodeableConcept = Field(description="Clinical identifier for the observation type")
    subject_reference: str = Field(description="Relative reference to the patient, e.g., 'Patient/10042'")
    effectiveDateTime: str = Field(description="ISO-8601 clinical timestamp when observation occurred")
    valueQuantity: Optional[Quantity] = Field(default=None, description="Quantitative measurement value if applicable")
    interpretation: Optional[CodeableConcept] = Field(default=None, description="Clinical interpretation, e.g., 'High', 'Normal'")

class ClinicalConsultationExtract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    encounter_id: str = Field(description="Unique encounter tracking identifier")
    patient_id: str = Field(description="De-identified patient identifier")
    observations: List[FHIRObservation] = Field(description="List of extracted clinical vital signs and laboratory observations")
    clinical_notes_summary: str = Field(description="Concise medical narrative summary of the encounter")
