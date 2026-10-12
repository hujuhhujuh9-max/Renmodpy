package org.renmodpy.validation;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract.Document;
import android.provider.DocumentsContract.Root;
import android.provider.DocumentsProvider;
import java.io.File;
import java.io.FileNotFoundException;

/** Local test documents behind the real Android picker and permission grants. */
public class FixtureDocuments extends DocumentsProvider {
    private static final String[] ROOT_COLUMNS = {Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE,
        Root.COLUMN_FLAGS, Root.COLUMN_MIME_TYPES, Root.COLUMN_AVAILABLE_BYTES};
    private static final String[] DOCUMENT_COLUMNS = {Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
        Document.COLUMN_MIME_TYPE, Document.COLUMN_FLAGS, Document.COLUMN_SIZE, Document.COLUMN_LAST_MODIFIED};

    private File directory() {
        File root = new File(getContext().getFilesDir(), "documents");
        root.mkdirs();
        return root;
    }

    private File file(String id) throws FileNotFoundException {
        if (id == null || id.contains("/") || id.contains("\\") || id.equals(".") || id.equals(".."))
            throw new FileNotFoundException("Invalid document");
        return id.equals("root") ? directory() : new File(directory(), id);
    }

    @Override public boolean onCreate() { directory(); return true; }
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor = new MatrixCursor(projection == null ? ROOT_COLUMNS : projection);
        MatrixCursor.RowBuilder row = cursor.newRow();
        row.add(Root.COLUMN_ROOT_ID, "fixture").add(Root.COLUMN_DOCUMENT_ID, "root")
            .add(Root.COLUMN_TITLE, "RenModPy fixtures").add(Root.COLUMN_FLAGS, Root.FLAG_SUPPORTS_CREATE | Root.FLAG_LOCAL_ONLY)
            .add(Root.COLUMN_MIME_TYPES, "*/*").add(Root.COLUMN_AVAILABLE_BYTES, directory().getFreeSpace());
        return cursor;
    }

    private void add(MatrixCursor cursor, String id) throws FileNotFoundException {
        File selected = file(id);
        if (!selected.exists()) throw new FileNotFoundException(id);
        cursor.newRow().add(Document.COLUMN_DOCUMENT_ID, id).add(Document.COLUMN_DISPLAY_NAME, id.equals("root") ? "RenModPy fixtures" : id)
            .add(Document.COLUMN_MIME_TYPE, selected.isDirectory() ? Document.MIME_TYPE_DIR : "application/json")
            .add(Document.COLUMN_FLAGS, selected.isDirectory() ? Document.FLAG_DIR_SUPPORTS_CREATE : Document.FLAG_SUPPORTS_WRITE)
            .add(Document.COLUMN_SIZE, selected.length()).add(Document.COLUMN_LAST_MODIFIED, selected.lastModified());
    }

    @Override public Cursor queryDocument(String id, String[] projection) throws FileNotFoundException {
        MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
        add(cursor, id); return cursor;
    }

    @Override public Cursor queryChildDocuments(String parent, String[] projection, String order) throws FileNotFoundException {
        MatrixCursor cursor = new MatrixCursor(projection == null ? DOCUMENT_COLUMNS : projection);
        if (!parent.equals("root")) throw new FileNotFoundException(parent);
        File[] children = directory().listFiles();
        if (children != null) for (File child : children) add(cursor, child.getName());
        return cursor;
    }

    @Override public String createDocument(String parent, String mime, String name) throws FileNotFoundException {
        if (!parent.equals("root")) throw new FileNotFoundException(parent);
        File target = file(name);
        try {
            if (!target.exists() && !target.createNewFile()) throw new FileNotFoundException(name);
        } catch (java.io.IOException error) { throw new FileNotFoundException(error.toString()); }
        return name;
    }

    @Override public ParcelFileDescriptor openDocument(String id, String mode, CancellationSignal cancel) throws FileNotFoundException {
        return ParcelFileDescriptor.open(file(id), ParcelFileDescriptor.parseMode(mode));
    }
}
