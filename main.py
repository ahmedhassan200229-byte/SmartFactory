import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles

# استيراد محرك المعالجة المكتوب في الملف السابق
from media_processor import AdvancedMediaProcessor

app = FastAPI(title="Media Downloader API")

# حماية CORS وتسهيل الاتصال من التطبيق أو المتصفح بدون قيود
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = AdvancedMediaProcessor()

# هياكل التحقق من البيانات المرسلة للـ API
class URLRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    urls: List[str]
    quality: str
    zip_name: str

@app.post("/api/analyze")
def analyze_url(request: URLRequest):
    """المسار الأول: لفحص الرابط واستخراج عناصر القائمة"""
    if not request.url:
        raise HTTPException(status_code=400, detail="الرجاء إدخال رابط صحيح")
    
    result = processor.extract_playlist_metadata(request.url)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error_message"])
    return result

@app.post("/api/download")
def download_media(request: DownloadRequest):
    """المسار الثاني: لتحميل المحتوى المختار وضغطه تم إرساله كـ ZIP"""
    if not request.urls:
        raise HTTPException(status_code=400, detail="لم يتم اختيار أي فيديو للتحميل")
    
    try:
        # 1. تنزيل الفيديوهات المحددة
        temp_dir = processor.download_selected_videos(
            video_urls=request.urls, 
            quality=request.quality
        )
        
        # 2. إنشاء الأرشيف المضغوط وتنظيف السيرفر
        zip_file_path = processor.archive_and_cleanup(
            folder_path=temp_dir, 
            zip_name=request.zip_name
        )
        
        # 3. إرجاع الملف فوراً للتحميل
        if os.path.exists(zip_file_path):
            return FileResponse(
                path=zip_file_path, 
                filename=zip_file_path, 
                media_type="application/zip"
            )
        else:
            raise HTTPException(status_code=500, detail="فشل إنشاء ملف الأرشيف")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# تشغيل واجهة الـ HTML التلقائية عند الدخول للموقع الرئيسي
# ملحوظة: تأكد من إنشاء مجلد باسم static وتضع به ملف index.html
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

