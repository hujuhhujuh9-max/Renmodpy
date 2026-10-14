package org.renpy.android;

import android.app.Activity;
import android.net.Uri;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Scoped document IO. Calls run on a Python worker, never the Android UI. */
public final class RenModPyDocuments {
    public static String readText(Activity activity, String location, int limit) throws Exception {
        Uri uri = Uri.parse(location);
        if (!"content".equals(uri.getScheme())) throw new IllegalArgumentException("Choose an Android document.");
        try (InputStream input = activity.getContentResolver().openInputStream(uri)) {
            if (input == null) throw new IllegalStateException("The document could not be opened.");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (bytes.size() + count > limit) throw new IllegalArgumentException("The document is too large.");
                bytes.write(buffer, 0, count);
            }
            return StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(bytes.toByteArray())).toString();
        }
    }

    public static boolean writeText(Activity activity, String location, String text) throws Exception {
        Uri uri = Uri.parse(location);
        if (!"content".equals(uri.getScheme())) throw new IllegalArgumentException("Choose an Android document.");
        try (OutputStream output = activity.getContentResolver().openOutputStream(uri, "wt")) {
            if (output == null) throw new IllegalStateException("The document could not be opened.");
            output.write(text.getBytes(StandardCharsets.UTF_8));
            output.flush();
        }
        return true;
    }
}
