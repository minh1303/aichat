from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from comfyui_client import ComfyUIClient

app = FastAPI(title="AI Image Generator API")
OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)
comfy = ComfyUIClient(output_dir=OUTPUT_DIR)
# ============================================
# CORS - Allow frontend to talk to backend
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CONFIG
# ============================================

class GenerateRequest(BaseModel):   
    prompt: str

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {"message": "🌸 AI Image Generator API", "status": "running"}

@app.post("/generate")
async def generate_image(request: GenerateRequest):
    if not request.prompt or len(request.prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    result = await comfy.generate_image(request.prompt)
    return result

@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Image not found")