"""Adjusts the generated Capacitor Android project for Spend Meter:
native Google sign-in, release signing from CI secrets, version numbers,
and the custom SmsReader plugin for reading bank transaction SMS."""
import os, re, sys, shutil

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

# 3. Add READ_SMS permission to AndroidManifest.xml
manifest = 'android/app/src/main/AndroidManifest.xml'
m = open(manifest).read()
if 'READ_SMS' not in m:
    # Insert just before the <application tag
    m = m.replace('<application', '<uses-permission android:name="android.permission.READ_SMS" />\n\n    <application', 1)
    open(manifest, 'w').write(m)
    print('READ_SMS permission added to AndroidManifest.xml')
else:
    print('READ_SMS permission already present')

# 4. Copy SmsPlugin.java into the Android source tree
this_dir    = os.path.dirname(os.path.abspath(__file__))
plugin_src  = os.path.join(this_dir, 'SmsPlugin.java')
plugin_dst  = 'android/app/src/main/java/com/safi/spendmeter/SmsPlugin.java'
shutil.copy(plugin_src, plugin_dst)
print('SmsPlugin.java installed at', plugin_dst)

# 5. Register SmsPlugin in MainActivity.java
main_activity = 'android/app/src/main/java/com/safi/spendmeter/MainActivity.java'
ma = open(main_activity).read()
if 'SmsPlugin' not in ma:
    # Replace the default empty class body with one that registers the plugin
    ma = ma.replace(
        'public class MainActivity extends BridgeActivity {}',
        '''public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(android.os.Bundle savedInstanceState) {
        registerPlugin(SmsPlugin.class);
        super.onCreate(savedInstanceState);
    }
}'''
    )
    open(main_activity, 'w').write(ma)
    print('SmsPlugin registered in MainActivity.java')
else:
    print('SmsPlugin already registered in MainActivity.java')
