[app]
title = Modern Messenger
package.name = modernmessenger
package.domain = org.yourname

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf

version = 1.0
requirements = python3,kivy,openssl

[buildozer]
log_level = 2

[app]
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

[app]
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,RECORD_AUDIO

[app]
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 33

[app]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.arch = arm64

[app]
log_level = 2

# Настройки для iOS
[app]
ios.ios_version = 14.0
ios.codesign.allowed = *