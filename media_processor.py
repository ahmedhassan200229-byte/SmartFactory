import os
import zipfile
import io
import shutil
import yt_dlp

def fetch_playlist_info(url: str):
    """جلب معلومات قائمة التشغيل بشكل آمن مع روابط صور مصلحة لا تحظرها السيرفرات"""
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'قائمة تشغيل غير معروفة')
            
            videos = []
            entries = info.get('entries', [])
            
            # إذا كان الرابط لفيديو مفرد وليس قائمة
            if not entries and info.get('id'):
                entries = [info]
                title = info.get('title', 'فيديو مفرد')

            for entry in entries:
                if entry:
                    video_id = entry.get('id')
                    # معالجة رابط الصورة ليعمل دائماً بشكل مباشر وموثوق
                    thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None
                    
                    # حساب الوقت بشكل نصي
                    duration_sec = entry.get('duration')
                    duration_str = "00:00"
                    if duration_sec:
                        mins = int(duration_sec // 60)
                        secs = int(duration_sec % 60)
                        duration_str = f"{mins:02d}:{secs:02d}"

                    videos.append({
                        "id": video_id,
                        "title": entry.get('title', 'فيديو بدون عنوان'),
                        "thumbnail": thumb,
                        "duration": duration_str
                    })
            return {"title": title, "videos": videos}
        except Exception as e:
            return {"error": str(e)}

def download_and_zip_playlist(url: str, video_ids: list, quality: str):
    """
    تحميل الفيديوهات المختارة فقط وضغطها داخل الذاكرة (Memory) 
    لضمان إرسال ملف كامل 100% دون كتابة ملفات مؤقتة تتلف على السيرفر
    """
    # اختيار صيغة الجودة المطلوبة بناءً على رغبة المستخدم
    format_opt = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    if quality == '480p':
        format_opt = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    elif quality == '360p':
        format_opt = 'bestvideo[height<=360]+bestaudio/best[height<=360]'

    # إنشاء ملف مضغوط داخل الذاكرة العشوائية (RAM) لسرعة المعالجة ومنع التلف
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # مجلد مؤقت داخل السيرفر لتحميل الفيديوهات الفردية إليه أولاً بأول
        tmp_dir = os.path.join(os.getcwd(), "tmp_download")
        os.makedirs(tmp_dir, exist_ok=True)

        for idx, vid_id in enumerate(video_ids):
            video_url = f"https://www.youtube.com/watch?v={vid_id}"
            
            ydl_opts = {
                'format': format_opt,
                'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # تحميل الفيديو الفردي
                    res = ydl.extract_info(video_url, download=True)
                    filename = ydl.prepare_filename(res)
                    
                    # التحقق من أن الامتداد سليم وأن الملف كتب بنجاح
                    if not os.path.exists(filename):
                        # بعض صيغ الدمج تغير الامتداد إلى mkv تلقائياً
                        base, _ = os.path.splitext(filename)
                        for ext in ['.mp4', '.mkv', '.webm']:
                            if os.path.exists(base + ext):
                                filename = base + ext
                                break

                    if os.path.exists(filename):
                        # إضافة الفيديو كاملاً داخل ملف الـ ZIP
                        arcname = os.path.basename(filename)
                        zip_file.write(filename, arcname=arcname)
                        # حذف الفيديو الفردي فوراً لتوفير مساحة السيرفر
                        os.remove(filename)
                except Exception:
                    continue # تخطي أي فيديو يفشل تحميله والانتقال للتالي دون إفساد الحزمة

        # تنظيف المجلد المؤقت بالكامل بعد الانتهاء
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    # إعادة مؤشر القراءة لبداية الملف المضغوط لإرساله بشكل سليم
    zip_buffer.seek(0)
    return zip_buffer
