"""Run the FastAPI server locally or on a hosting platform like Render."""

import os

import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
