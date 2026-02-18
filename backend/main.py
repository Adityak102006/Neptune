"""
FastAPI backend for Local Image Similarity Search.
Provides endpoints for indexing image directories and searching by similarity.
"""

import os
import io
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .model import embedder
from .indexer import image_index

# Path to the built frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="Neptune - Image Similarity Search", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IndexRequest(BaseModel):
    directory: str


@app.get("/api/status")
def get_status():
    """Return current index status."""
    return {
        "indexed_count": image_index.indexed_count,
        "indexed_directory": image_index.indexed_directory,
        "ready": image_index.embeddings is not None,
    }


@app.post("/api/index")
def index_directory(request: IndexRequest):
    """Index all images in the given directory."""
    directory = request.directory.strip()
    if not directory:
        raise HTTPException(status_code=400, detail="Directory path is required.")
    if not os.path.isdir(directory):
        raise HTTPException(status_code=400, detail=f"Directory not found: {directory}")

    try:
        result = image_index.build_index(directory)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.post("/api/search")
async def search_similar(
    file: UploadFile = File(...),
    top_k: int = Query(20, ge=1, le=100),
):
    """Search for images similar to the uploaded image."""
    if image_index.embeddings is None:
        raise HTTPException(
            status_code=400,
            detail="No images indexed yet. Please index a folder first.",
        )

    # Save uploaded file to a temp location
    try:
        contents = await file.read()
        suffix = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Compute embedding for the query image
        query_embedding = embedder.get_embedding(tmp_path)

        # Search the index
        results = image_index.search_similar(query_embedding, top_k=top_k)

        return {"results": results, "query_filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.get("/api/images")
def serve_image(path: str = Query(..., description="Absolute path to local image")):
    """Serve a local image file to the frontend."""
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Image file not found.")

    # Security: only serve files from the indexed directory
    if image_index.indexed_directory:
        abs_path = os.path.abspath(path)
        abs_indexed = os.path.abspath(image_index.indexed_directory)
        if not abs_path.startswith(abs_indexed):
            raise HTTPException(status_code=403, detail="Access denied.")

    return FileResponse(path)


# ── Serve built frontend ────────────────────────────────
if FRONTEND_DIR.is_dir():
    # Serve static assets (JS, CSS, images) from the Vite build
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return HTMLResponse((FRONTEND_DIR / "index.html").read_text())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
