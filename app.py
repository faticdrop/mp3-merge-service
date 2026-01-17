import os, tempfile, subprocess
from typing import List
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI()

class MergeRequest(BaseModel):
    urls: List[HttpUrl]
    output_name: str = "merged.mp3"

def download(url: str, path: str):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)

@app.post("/merge")
def merge(req: MergeRequest):
    if len(req.urls) < 2:
        raise HTTPException(400, "At least 2 URLs required")

    with tempfile.TemporaryDirectory() as d:
        files = []
        for i, url in enumerate(req.urls):
            p = os.path.join(d, f"{i}.mp3")
            download(str(url), p)
            files.append(p)

        lst = os.path.join(d, "list.txt")
        with open(lst, "w") as f:
            for fp in files:
                f.write(f"file '{fp}'\n")

        out = os.path.join(d, req.output_name)
        subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
            check=True
        )

        return FileResponse(out, media_type="audio/mpeg", filename=req.output_name)
