"""Integrated FastAPI backend for a modular multi-stage NLP-to-SQL pipeline."""

import sqlite3
import traceback
from contextlib import contextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from generator_service import SQLGeneratorService
from optimization_service import SQLOptimizationService
from pipeline_service import NL2SQLPipelineService
from schema_service import build_schema_bundle
from validation_service import SQLValidationService


HF_MODEL_ID = "hansini1211/nl2sql"
DB_PATH = "company.db"

print(f"Loading model pipeline from {HF_MODEL_ID} ...")
generator_service = SQLGeneratorService(model_id=HF_MODEL_ID)
validation_service = SQLValidationService()
optimization_service = SQLOptimizationService()
pipeline_service = NL2SQLPipelineService(
    generator=generator_service,
    validator=validation_service,
    optimizer=optimization_service,
)
print("Pipeline services loaded!")


app = FastAPI(title="NLP-to-SQL API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


class QueryRequest(BaseModel):
    """Incoming query payload."""

    question: str


class SchemaTable(BaseModel):
    """Schema details for one database table."""

    table_name: str
    columns: List[str]
    sample_rows: List[Dict[str, Any]]


class PipelineTrace(BaseModel):
    """Intermediate pipeline values for debugging and observability."""

    schema_text: str
    headers: List[str]
    generated_input: str
    validator_intent: str


class QueryResponse(BaseModel):
    """End-to-end response from the integrated pipeline."""

    question: str
    schema: List[SchemaTable]
    generated_sql: str
    validated_sql: str
    optimized_sql: str
    final_sql: str
    result: List[Dict[str, Any]]
    optimization: Dict[str, Any]
    intent: str
    pipeline_trace: PipelineTrace


@contextmanager
def get_db():
    """Yield a SQLite connection for one request."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@app.get("/")
def root() -> FileResponse:
    """Serve the frontend entry point."""
    return FileResponse("frontend/index.html")


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """Run the full schema, generation, validation, execution, and optimization pipeline."""
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        with get_db() as conn:
            pipeline_output = pipeline_service.run(question, conn)

        return QueryResponse(
            question=question,
            schema=[SchemaTable(**table) for table in pipeline_output["schema_bundle"]["tables"]],
            generated_sql=pipeline_output["generated_sql"],
            validated_sql=pipeline_output["validated_sql"],
            optimized_sql=pipeline_output["optimized_sql"],
            final_sql=pipeline_output["final_sql"],
            result=pipeline_output["result"],
            optimization=pipeline_output["optimization"],
            intent=pipeline_output["validation"].get("intent", "SELECT"),
            pipeline_trace=PipelineTrace(
                schema_text=pipeline_output["schema_bundle"]["schema_text"],
                headers=pipeline_output["schema_bundle"]["headers"],
                generated_input=pipeline_output["generated_input"],
                validator_intent=pipeline_output["validation"].get("intent", "SELECT"),
            ),
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/schema")
def schema() -> Dict[str, Any]:
    """Return the live schema extracted from the database."""
    with get_db() as conn:
        return build_schema_bundle(conn)


@app.get("/health")
def health() -> Dict[str, str]:
    """Return API health details."""
    return {"status": "ok", "model": HF_MODEL_ID}
