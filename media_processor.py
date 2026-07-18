import os
import zipfile
import shutil
import yt_dlp

def fetch_playlist_info(url: str):
    """فحص الرابط وسحب البيانات التكنولوجية المباشرة للفيديوهات"""
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Smart Playlist')
            
            videos = []
            entries = info.get('entries', [])
            
            # إذا كان الرابط لفيديو منفرد وليس قائمة تشغيل
            if not entries and info.get('id'):
                entries = [info]
                title = info.get('title', 'Single Stream')

            for entry in entries:
                if entry:
                    video_id = entry.get('id')
                    # معالجة روابط الصور لتعمل دائماً بشكل مباشر وصحيح دون حظر
                    thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None
                    
                    duration_sec = entry.get('duration')
                    duration_str = "00:00"
                    if duration_sec:
                        mins = int(duration_sec // 60)
                        secs = int(duration_sec % 60)
                        duration_str = f"{mins:02d}:{secs:02d}"

                    videos.append({
                        "id": video_id,
                        "title": entry.get('title', 'Untitled Video'),
                        "thumbnail": thumb,
                        "duration": duration_str
                    })
            return {"title": title, "videos": videos}
        except Exception as e:
            return {"error": str(e)}

def download_and_zip_playlist(url: str, video_ids: list, quality: str):
    """
    التحميل والضغط الميكانيكي المستقر على القرص الصلب لتفادي انقطاع السيرفر
    """
    # اختيار صيغة الجودة المطلوبة بناءً على رغبة المستخدم
    format_opt = 'best[height<=720]/best'
    if quality == '480p':
        format_opt = 'best[height<=480]/best'
    elif quality == '360p':
        format_opt = 'best[height<=360]/best'

    # إنشاء مجلد عمل مؤقت حقيقي على الهارد ديسك الخاص بالسيرفر
    workspace_dir = os.path.join(os.getcwd(), "factory_workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    
    # تحديد مسار ملف الـ ZIP النهائي
    zip_path = os.path.join(os.getcwd(), "output_archive.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # التحميل الفعلي للفيديوهات المختارة فقط داخل المجلد المؤقت
    for vid_id in video_ids:
        video_url = f"https://www.youtube.com/watch?v={vid_id}"
        ydl_opts = {
            'format': format_opt,
            'outtmpl': os.path.join(workspace_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'external_downloader': 'builtin'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except Exception:
                continue # تخطي الفيديو الذي يسبب مشكلة والانتقال للتالي

    # ضغط المجلد المؤقت بالكامل إلى ملف ZIP حقيقي مستقر 100%
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(workspace_dir):
            for file in files:
                file_full_path = os.path.join(root, file)
                zipf.write(file_full_path, os.path.basename(file_full_path))

    # إزالة مجلد الفيديوهات المؤقتة لتوفير مساحة السيرفر فوراً
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)

    return zip_path
