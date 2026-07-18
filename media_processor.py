import os
import zipfile
import shutil
import tempfile
from typing import List, Dict, Any, Optional

# تأكد من تثبيت وتحديث المكتبة في السيرفر: pip install -U yt-dlp
import yt_dlp

class AdvancedMediaProcessor:
    """
    فصل متكامل لمعالجة وتحميل القوائم والوسائط المفتوحة من مختلف المنصات.
    يدعم استخراج القوائم كاملة، التحميل الانتقائي، تحديد الجودة، والضغط التلقائي.
    """

    def __init__(self):
        # إعدادات الفحص السريع لاستخراج البيانات الوصفية فقط دون تحميل أي ملفات
        self.ydl_opts_metadata = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,    # مسح القائمة بشكل مسطح وسريع جداً لجلب العناصر
            'skip_download': True,   # عدم تحميل أي محتوى في مرحلة الفحص
            'force_generic_extractor': False,
        }

    # ------------------- الدالة الأولى: استخراج بيانات القائمة أو الصفحة كاملة -------------------
    def extract_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """
        تستقبل رابط قائمة تشغيل أو صفحة ريلز، وتستخرج الأسماء، الروابط والصور المصغرة لكل فيديو.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_metadata) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # التحقق مما إذا كان الرابط يحتوي على عناصر متعددة (قائمة تشغيل / صفحة)
                if 'entries' in info:
                    videos_list = []
                    for entry in info['entries']:
                        if entry:  # التأكد من أن العنصر يحتوي على بيانات صالحة
                            video_url = entry.get('url') or entry.get('webpage_url')
                            if not video_url and entry.get('id'):
                                video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"

                            videos_list.append({
                                "id": entry.get('id'),
                                "title": entry.get('title', 'بدون عنوان'),
                                "url": video_url,
                                "thumbnail": entry.get('thumbnail', None)
                            })
                    
                    return {
                        "status": "success",
                        "type": "playlist",
                        "playlist_title": info.get('title', 'media_package'),
                        "total_videos": len(videos_list),
                        "videos": videos_list  # هذه المصفوفة التي تُعرض للمستخدم للاختيار منها
                    }
                else:
                    # إذا كان الرابط لفيديو فردي وليس قائمة
                    return {
                        "status": "success",
                        "type": "single_video",
                        "playlist_title": info.get('title', 'single_video'),
                        "videos": [{
                            "id": info.get('id'),
                            "title": info.get('title', 'بدون عنوان'),
                            "url": info.get('webpage_url', url),
                            "thumbnail": info.get('thumbnail', None)
                        }]
                    }
        except Exception as e:
            return {
                "status": "error",
                "source_url": url,
                "error_message": str(e)
            }

    # ------------------- الدالة الثانية: تحميل الفيديوهات المختارة فقط بجودة محددة -------------------
    def download_selected_videos(self, video_urls: List[str], quality: str = "720p", temp_folder: Optional[str] = None) -> str:
        """
        تستقبل روابط الفيديوهات المحددة فقط من قبل المستخدم وتنزّلها داخل مجلد مؤقت بالجودة المطلوبة.
        """
        if temp_folder is None:
            temp_folder = tempfile.mkdtemp(prefix="media_downloads_")
        
        # إدارة وتخصيص الجودة بناءً على اختيار المستخدم
        if quality.lower() == "mp3":
            format_option = 'bestaudio/best'
            postprocessors_opts = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            merge_format = None
        else:
            format_option = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best'
            postprocessors_opts = []
            merge_format = 'mp4'

        download_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(temp_folder, '%(title)s.%(ext)s'),  # حفظ الملف باسم الفيديو الأصلي
            'format': format_option,
            'merge_output_format': merge_format,
            'postprocessors': postprocessors_opts,
            'ignoreerrors': True,  # تخطي أي فيديو يفشل تحميله وإكمال بقية القائمة
        }

        with yt_dlp.YoutubeDL(download_opts) as ydl:
            for url in video_urls:
                if url:
                    try:
                        ydl.download([url])
                    except Exception as e:
                        print(f"[خطأ في النظام] تعذر تحميل الرابط {url}: {e}")

        return temp_folder

    # ------------------- الدالة الثالثة: أرشفة المجلد إلى ملف ZIP والتنظيف الفوري -------------------
    def archive_and_cleanup(self, folder_path: str, zip_name: str = "media_package") -> str:
        """
        تضغط المجلد المؤقت بالكامل إلى ملف .zip، ثم تحذف الفيديوهات والمجلد الأصلي لتوفير مساحة السيرفر.
        """
        safe_zip_name = "".join([c for c in zip_name if c.isalpha() or c.isdigit() or c in ' _-']).rstrip()
        if not safe_zip_name:
            safe_zip_name = "media_package"
            
        zip_path = f"{safe_zip_name}.zip"
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"المجلد المؤقت غير موجود: {folder_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, start=folder_path)
                    zipf.write(full_path, arcname)
        
        # حذف المجلد المؤقت فوراً للحفاظ على الموارد
        shutil.rmtree(folder_path, ignore_errors=True)
        print(f"[نظام الحفظ] تم تنظيف السيرفر وحذف المجلد المؤقت: {folder_path}")
        
        return zip_path
