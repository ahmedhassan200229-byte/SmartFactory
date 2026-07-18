from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# استدعاء الدوال المطورة من ملف المعالجة
from media_processor import fetch_playlist_info, download_and_zip_playlist

app = FastAPI(title="Smart Media Downloader Server")

# ربط المجلد الاستاتيكي لخدمة واجهة المستخدم HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

class DownloadRequest(BaseModel):
    url: str
    quality: str
    video_ids: list
    playlist_title: str

@app.get("/")
def read_root():
    # فتح الواجهة بشكل تلقائي فور فتح السيرفر
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/api/analyze")
def analyze_url(url: str = Query(..., description="رابط قائمة التشغيل المراد فحصها")):
    if not url:
        raise HTTPException(status_code=400, detail="الرجاء تزويد الرابط بشكل صحيح")
    
    result = fetch_playlist_info(url)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/download-zip")
async def download_zip_endpoint(req: DownloadRequest):
    if not req.video_ids:
        raise HTTPException(status_code=400, detail="لم يتم تحديد أي فيديوهات لتحميلها")
    
    try:
        # توليد حزمة الـ ZIP المكتملة داخل الذاكرة
        zip_io = download_and_zip_playlist(req.url, req.video_ids, req.quality)
        
        # صياغة اسم الملف النهائي بشكل آمن
        safe_title = "".join([c for c in req.playlist_title if c.isalpha() or c.isdigit() or c in ' ']).rstrip()
        filename = f"{safe_title or 'playlist'}.zip"
        
        # إرسال الملف دفعة واحدة بشكل متدفق للمتصفح لحل مشكلة الملفات التالفة
        return StreamingResponse(
            zip_io,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء الضغط: {str(e)}")
