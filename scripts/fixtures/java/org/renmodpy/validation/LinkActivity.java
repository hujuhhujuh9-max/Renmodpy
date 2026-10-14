package org.renmodpy.validation;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Process;
import android.widget.Button;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/** Offline external caller: a real tap launches a VIEW Intent without task flags. */
public class LinkActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String uri = getIntent().getStringExtra("record_uri");
        Button button = new Button(this);
        button.setText("Open saved Record");
        button.setAllCaps(false);
        button.setTextSize(26);
        button.setOnClickListener(view -> {
            JSONObject receipt = new JSONObject();
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(uri));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            intent.setPackage("org.renmodpy.example");
            try {
                receipt.put("uri", uri);
                receipt.put("action", intent.getAction());
                receipt.put("flags", intent.getFlags());
                receipt.put("uid", Process.myUid());
                receipt.put("task_id", getTaskId());
                startActivity(intent);
                receipt.put("result", "launched");
            } catch (Exception error) {
                try {
                    receipt.put("result", "failed");
                    receipt.put("error", error.toString());
                } catch (Exception ignored) { }
            }
            try (FileOutputStream output = new FileOutputStream(new File(getFilesDir(), "link.json"))) {
                output.write(receipt.toString().getBytes(StandardCharsets.UTF_8));
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        setContentView(button);
    }
}
