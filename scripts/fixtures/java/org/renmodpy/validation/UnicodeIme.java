package org.renmodpy.validation;

import android.inputmethodservice.InputMethodService;
import android.os.Looper;
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
                try (FileOutputStream output = new FileOutputStream(new File(getFilesDir(), "ime.json"))) {
                    output.write(report.toString().getBytes(StandardCharsets.UTF_8));
                }
            } catch (Exception error) { throw new RuntimeException(error); }
        });
        compose.setOnClickListener(view -> {
            InputConnection input = getCurrentInputConnection();
            if (input != null) {
                input.setComposingText("cafe", 1);
                input.setComposingText("café", 1);
                input.commitText("café", 1);
                input.finishComposingText();
            }
        });
        row.addView(compose);
        return row;
    }
}
