[app]
title = Smart Factory
package.name = smartfactory
package.domain = org.smartfactory
source.dir = .
source.include_ext = py,png,jpg,kv,atlas
version = 1.0

# المكتبات المطلوبة لتشغيل كود تطبيقك
requirements = python3,kivy==2.2.1,kivymd,pyserial,requests,certifi,urllib3

orientation = portrait
fullscreen = 0

# الصلاحيات الأساسية
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

# جعل الحزم تختار تلقائياً لتجنب تعارض النسخ
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
