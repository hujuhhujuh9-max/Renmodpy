package org.renmodpy.validation;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Process;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.json.JSONObject;

/** Disposable offline receiver. No messages, accounts, network or production role. */
public class ReceiverActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        JSONObject receipt = new JSONObject();
        try {
            Intent intent = getIntent();
            Uri uri = (Uri) intent.getParcelableExtra(Intent.EXTRA_STREAM);
            byte[] data;
            if (uri != null) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                try (InputStream input = getContentResolver().openInputStream(uri)) {
                    byte[] buffer = new byte[8192];
                    int count;
                    while ((count = input.read(buffer)) != -1) {
                        if (bytes.size() + count > 8 * 1024 * 1024) throw new IllegalArgumentException("Too large");
                        bytes.write(buffer, 0, count);
                    }
                }
                data = bytes.toByteArray();
                receipt.put("uri", uri.toString());
                receipt.put("scheme", uri.getScheme());
                receipt.put("read_grant", (intent.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION) != 0);
            } else {
                data = intent.getStringExtra(Intent.EXTRA_TEXT).getBytes(StandardCharsets.UTF_8);
            }
            StringBuilder digest = new StringBuilder();
            for (byte value : MessageDigest.getInstance("SHA-256").digest(data)) digest.append(String.format("%02x", value & 255));
            receipt.put("action", intent.getAction());
            receipt.put("mime", intent.getType());
            receipt.put("text", new String(data, StandardCharsets.UTF_8));
            receipt.put("sha256", digest.toString());
            receipt.put("uid", Process.myUid());
            receipt.put("result", "passed");
        } catch (Exception error) {
            try { receipt.put("result", "failed"); receipt.put("error", error.toString()); } catch (Exception ignored) {}
        }
        try (FileOutputStream output = new FileOutputStream(new File(getFilesDir(), "received.json"))) {
            output.write(receipt.toString().getBytes(StandardCharsets.UTF_8));
        } catch (Exception error) { throw new RuntimeException(error); }
        TextView view = new TextView(this);
        view.setText("RenModPy validation receiver\n" + receipt.optString("result"));
        view.setTextSize(26);
        setContentView(view);
    }
}
