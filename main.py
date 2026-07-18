from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.background import BackgroundTasks
import os

# استدعاء الدوال المطورة من ملف المعالجة الميكانيكي
from media_processor import fetch_playlist_info, download_and_zip_playlist

app = FastAPI(title="Smart Factory Downloader Core")

# ربط المجلد الاستاتيكي لخدمة واجهة المستخدم HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

class DownloadRequest(BaseModel):
    url: str
    quality: str
    video_ids: list
    playlist_title: str

def cleanup_file(path: str):
    """دالة خلفية لتنظيف السيرفر وحذف الـ ZIP بعد التحميل الناجح للمستخدم"""
    if os.path.exists(path):
        os.remove(path)

@app.get("/")
def read_root():
    # فتح الواجهة بشكل تلقائي فور فتح السيرفر
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/api/analyze")
def analyze_url(url: str = Query(..., description="Target Link")):
    if not url:
        raise HTTPException(status_code=400, detail="Missing Link")
    result = fetch_playlist_info(url)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/download-zip")
async def download_zip_endpoint(req: DownloadRequest, background_tasks: BackgroundTasks):
    if not req.video_ids:
        raise HTTPException(status_code=400, detail="No selected elements")
    
    try:
        # توليد الملف الفعلي المستقر على القرص الصلب
        zip_file_path = download_and_zip_playlist(req.url, req.video_ids, req.quality)
        
        if not os.path.exists(zip_file_path) or os.path.getsize(zip_file_path) < 100:
            raise HTTPException(status_code=500, detail="Compilation error")

        # إرسال الملف الفعلي مع تشغيل دالة المسح التلقائي في الخلفية لحفظ نظافة السيرفر
        background_tasks.add_task(cleanup_file, zip_file_path)
        
        return FileResponse(
            zip_file_path,
            media_type="application/zip",
            filename=f"factory_archive.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
