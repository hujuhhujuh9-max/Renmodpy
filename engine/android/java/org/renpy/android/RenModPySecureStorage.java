package org.renpy.android;

import android.app.Activity;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import android.util.Base64;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.MessageDigest;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import org.json.JSONObject;

/** App-private, non-backup ciphertext. Keys remain in Android Keystore. */
public final class RenModPySecureStorage {
    private static final String ALIAS = "renmodpy.secure.v1";

    private static SecretKey key(boolean create) throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (!store.containsAlias(ALIAS)) {
            if (!create) throw new IllegalStateException("The storage key is unavailable.");
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build());
            return generator.generateKey();
        }
        return (SecretKey) store.getKey(ALIAS, null);
    }

    private static AtomicFile file(Activity activity, String name) throws Exception {
        File directory = new File(activity.getNoBackupFilesDir(), "renmodpy-secure");
        if (!directory.exists() && !directory.mkdirs()) throw new IllegalStateException("Private storage is unavailable.");
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(name.getBytes(StandardCharsets.UTF_8));
        StringBuilder filename = new StringBuilder();
        for (byte value : digest) {
            if ((value & 255) < 16) filename.append('0');
            filename.append(Integer.toHexString(value & 255));
        }
        return new AtomicFile(new File(directory, filename + ".json"));
    }

    public static synchronized boolean set(Activity activity, String name, String value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key(true));
        cipher.updateAAD(name.getBytes(StandardCharsets.UTF_8));
        JSONObject data = new JSONObject();
        data.put("version", 1);
        data.put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP));
        data.put("ciphertext", Base64.encodeToString(cipher.doFinal(value.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP));
        AtomicFile target = file(activity, name);
        FileOutputStream output = null;
        try {
            output = target.startWrite();
            output.write(data.toString().getBytes(StandardCharsets.UTF_8));
            target.finishWrite(output);
            return true;
        } catch (Exception error) {
            if (output != null) target.failWrite(output);
            throw error;
        }
    }

    public static synchronized String get(Activity activity, String name) throws Exception {
        AtomicFile target = file(activity, name);
        if (!target.getBaseFile().exists() && !new File(target.getBaseFile() + ".bak").exists()) return null;
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (FileInputStream input = target.openRead()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (bytes.size() + count > 131072) throw new IllegalStateException("Private storage is corrupt.");
                bytes.write(buffer, 0, count);
            }
        }
        JSONObject data = new JSONObject(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
        if (data.getInt("version") != 1) throw new IllegalStateException("Private storage format is unsupported.");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(false), new GCMParameterSpec(128, Base64.decode(data.getString("iv"), Base64.NO_WRAP)));
        cipher.updateAAD(name.getBytes(StandardCharsets.UTF_8));
        return new String(cipher.doFinal(Base64.decode(data.getString("ciphertext"), Base64.NO_WRAP)), StandardCharsets.UTF_8);
    }

    public static synchronized boolean delete(Activity activity, String name) throws Exception {
        AtomicFile target = file(activity, name);
        boolean existed = target.getBaseFile().exists() || new File(target.getBaseFile() + ".bak").exists();
        target.delete();
        if (target.getBaseFile().exists() || new File(target.getBaseFile() + ".bak").exists())
            throw new IllegalStateException("Private storage could not be deleted.");
        return existed;
    }
}
