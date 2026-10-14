package org.renmodpy.validation;

import android.inputmethodservice.InputMethodService;
import android.os.Looper;
import android.util.AtomicFile;
import android.view.View;
import android.view.inputmethod.InputConnection;
import android.widget.Button;
import android.widget.LinearLayout;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/** Exercises actual InputConnection composition in a disposable emulator. */
public class UnicodeIme extends InputMethodService {
    private void report(String name, JSONObject data) throws Exception {
        AtomicFile target = new AtomicFile(new File(getFilesDir(), name));
        FileOutputStream output = target.startWrite();
        try {
            output.write(data.toString().getBytes(StandardCharsets.UTF_8));
            target.finishWrite(output);
        } catch (Exception error) {
            target.failWrite(output);
            throw error;
        }
    }

    @Override public View onCreateInputView() {
        LinearLayout row = new LinearLayout(this);
        Button compose = new Button(this);
        compose.setText("Compose café");
        compose.setTextSize(24);
        compose.setMinHeight(96);
        compose.addOnLayoutChangeListener((view, l, t, r, b, oldL, oldT, oldR, oldB) -> {
            if (view.getWidth() == 0) return;
            try {
                int[] position = new int[2]; view.getLocationOnScreen(position);
                JSONObject report = new JSONObject();
                report.put("x", position[0] + view.getWidth() / 2);
                report.put("y", position[1] + view.getHeight() / 2);
                report.put("ui_thread", Looper.myLooper() == Looper.getMainLooper());
                report("ime.json", report);
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        compose.setOnClickListener(view -> {
            try {
                InputConnection input = getCurrentInputConnection();
                JSONObject result = new JSONObject();
                result.put("input_connection", input != null);
                result.put("ui_thread", Looper.myLooper() == Looper.getMainLooper());
                if (input != null) {
                    result.put("compose_first", input.setComposingText("cafe", 1));
                    result.put("compose_final", input.setComposingText("café", 1));
                    result.put("commit", input.commitText("café", 1));
                    result.put("finish", input.finishComposingText());
                }
                report("composition.json", result);
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        row.addView(compose);
        return row;
    }
}
