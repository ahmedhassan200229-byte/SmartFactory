[app]
title = Smart Factory
package.name = smartfactory
package.domain = org.smartfactory
source.dir = .
source.include_ext = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.2.1,kivymd,pyserial,requests,certifi,urllib3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
