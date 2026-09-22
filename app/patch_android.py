"""Adjusts the generated Capacitor Android project for Spend Meter:
native Google sign-in, release signing from CI secrets, and version numbers."""
import os, re, sys

build_no = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# 1. Turn on the Google provider in @capacitor-firebase/authentication.
vg = 'android/variables.gradle'
s = open(vg).read()
if 'rgcfaIncludeGoogle' not in s:
    s = s.replace('ext {', 'ext {\n    rgcfaIncludeGoogle = true', 1)
open(vg, 'w').write(s)

# 2. Release signing (keystore path/password come from env vars) + version.
ag = 'android/app/build.gradle'
s = open(ag).read()
signing = '''
    signingConfigs {
        release {
            storeFile file(System.getenv("SM_KEYSTORE_PATH"))
            storePassword System.getenv("SM_KEYSTORE_PASSWORD")
            keyAlias "spendmeter"
            keyPassword System.getenv("SM_KEYSTORE_PASSWORD")
        }
    }
'''
if 'signingConfigs' not in s:
    s = s.replace('android {', 'android {' + signing, 1)
    s = s.replace('release {\n            minifyEnabled false',
                  'release {\n            signingConfig signingConfigs.release\n            minifyEnabled false', 1)
s = re.sub(r'versionCode \d+', f'versionCode {build_no}', s)
s = re.sub(r'versionName "[^"]*"', f'versionName "1.0.{build_no}"', s)
open(ag, 'w').write(s)
assert 'signingConfig signingConfigs.release' in s, 'signing patch failed'
print('Android project patched, build', build_no)
