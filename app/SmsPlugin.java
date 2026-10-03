package com.safi.spendmeter;

import android.Manifest;
import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/**
 * SmsReader — Capacitor plugin for SpendMeter.
 * Reads the SMS inbox for the last 24 hours and returns all messages.
 * The JavaScript layer then filters and parses bank transaction alerts.
 *
 * Permissions: android.permission.READ_SMS (requested at runtime).
 */
@CapacitorPlugin(
    name = "SmsReader",
    permissions = {
        @Permission(
            strings = { Manifest.permission.READ_SMS },
            alias   = "readSms"
        )
    }
)
public class SmsPlugin extends Plugin {

    /** Called from JS: Capacitor.Plugins.SmsReader.readRecentSms() */
    @PluginMethod
    public void readRecentSms(PluginCall call) {
        // Request READ_SMS at runtime if not yet granted
        if (!getPermissionState("readSms")
                .equals(com.getcapacitor.PermissionState.GRANTED)) {
            requestPermissionForAlias("readSms", call, "smsPermissionsCallback");
            return;
        }
        doReadSms(call);
    }

    @PermissionCallback
    private void smsPermissionsCallback(PluginCall call) {
        if (getPermissionState("readSms")
                .equals(com.getcapacitor.PermissionState.GRANTED)) {
            doReadSms(call);
        } else {
            call.reject("READ_SMS permission denied by user");
        }
    }

    private void doReadSms(PluginCall call) {
        try {
            // Last 24 hours
            long since = System.currentTimeMillis() - (30L * 24L * 60 * 60 * 1000); // last 30 days
            ContentResolver cr  = getContext().getContentResolver();
            Uri              uri = Uri.parse("content://sms/inbox");

            Cursor cursor = cr.query(
                uri,
                new String[]{ "address", "body", "date" },
                "date > ?",
                new String[]{ String.valueOf(since) },
                "date DESC"
            );

            JSArray messages = new JSArray();
            if (cursor != null) {
                while (cursor.moveToNext()) {
                    JSObject msg = new JSObject();
                    msg.put("address", cursor.getString(0));
                    msg.put("body",    cursor.getString(1));
                    msg.put("date",    cursor.getLong(2));
                    messages.put(msg);
                }
                cursor.close();
            }

            JSObject result = new JSObject();
            result.put("messages", messages);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Failed to read SMS inbox: " + e.getMessage());
        }
    }
}
