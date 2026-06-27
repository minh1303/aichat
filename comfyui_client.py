import json
import httpx
import random
import asyncio
import base64
import os
from datetime import datetime

class ComfyUIClient:
    def __init__(self, base_url="http://localhost:8188", output_dir="generated_images"):
        self.base_url = base_url
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    async def generate_image(self, prompt, workflow_path="workflow.json"):
        """Generate an image using ComfyUI and save it to disk"""
        
        # Load workflow
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
        
        # Set the prompt - node 2 uses "value" not "text"
        if "2" in workflow and "inputs" in workflow["2"]:
            workflow["2"]["inputs"]["value"] = prompt
        else:
            # Fallback: find any node with "value" field
            for node_id, node_data in workflow.items():
                if "value" in node_data.get("inputs", {}):
                    workflow[node_id]["inputs"]["value"] = prompt
                    break
        
        # Set random seed in KSampler
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "KSampler":
                workflow[node_id]["inputs"]["seed"] = random.randint(1, 1000000000)
                break
        
        # Send to ComfyUI
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow}
            )
            
            if response.status_code != 200:
                return {"error": f"ComfyUI error: {response.status_code}"}
            
            data = response.json()
            prompt_id = data.get("prompt_id")
            
            if not prompt_id:
                return {"error": "No prompt_id returned"}
            
            # Wait for and get the image
            image_data = await self._wait_for_image(prompt_id)
            
            if image_data:
                # Save the image to disk
                filename = self._save_image(image_data, prompt)
                
                # Generate the URL to access the image
                image_url = f"/images/{filename}"
                
                return {
                    "status": "success",
                    "prompt": prompt,
                    "filename": filename,
                    "image_url": image_url,
                    "full_url": f"http://localhost:5000{image_url}"
                }
            else:
                return {"status": "processing", "prompt": prompt, "prompt_id": prompt_id}
    
    def _save_image(self, image_data, prompt):
        """Save image to disk and return filename"""
        # Create a safe filename from the prompt
        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in " ._-").strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_prompt}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save the image
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        print(f"✅ Image saved: {filepath}")
        return filename
    
    async def _wait_for_image(self, prompt_id, timeout=60, check_interval=2):
        """Async poll ComfyUI for the generated image and return image data"""
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    # Check history for the completed prompt
                    response = await client.get(
                        f"{self.base_url}/history/{prompt_id}"
                    )
                    
                    if response.status_code == 200:
                        history = response.json()
                        if prompt_id in history and "outputs" in history[prompt_id]:
                            outputs = history[prompt_id]["outputs"]
                            
                            # Find the first image output
                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    images = node_output["images"]
                                    if images:
                                        filename = images[0]["filename"]
                                        subfolder = images[0].get("subfolder", "")
                                        folder_type = images[0].get("type", "output")
                                        
                                        # Get the actual image data
                                        image_response = await client.get(
                                            f"{self.base_url}/view",
                                            params={
                                                "filename": filename,
                                                "subfolder": subfolder,
                                                "type": folder_type
                                            }
                                        )
                                        
                                        if image_response.status_code == 200:
                                            return image_response.content
                                        
                                        # Fallback: try without subfolder/type
                                        image_response = await client.get(
                                            f"{self.base_url}/view",
                                            params={"filename": filename}
                                        )
                                        
                                        if image_response.status_code == 200:
                                            return image_response.content
                
                except Exception as e:
                    print(f"Error checking history: {e}")
                
                await asyncio.sleep(check_interval)
        
        return None