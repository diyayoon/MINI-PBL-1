import base64
import os
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory, url_for

from stego import embed_lsb_2bit, extract_lsb_2bit


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "Front-end"
STORAGE_DIR = BACKEND_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="/static",
)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _get_extension(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def _validate_file(file_storage) -> None:
    extension = _get_extension(file_storage.filename)

    if extension not in ALLOWED_EXTS:
        abort(
            415,
            description=(
                f"Ekstensi tidak didukung: {extension}. "
                "Gunakan PNG, JPG, JPEG, atau WebP."
            ),
        )


def _save_upload(file_storage, prefix: str = ""):
    _validate_file(file_storage)

    extension = _get_extension(file_storage.filename)
    filename = f"{prefix}{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    file_storage.save(file_path)

    return file_path, filename, extension


@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/encrypt")
def api_encrypt():
    original = request.files.get("original")
    cover = request.files.get("cover")
    secret_key = (request.form.get("secret_key") or "").strip()

    if not original or not cover:
        return jsonify(ok=False, error="Upload 'original' dan 'cover'."), 400

    if not secret_key:
        return jsonify(ok=False, error="Secret key wajib diisi."), 400

    original_path, _, original_ext = _save_upload(original, "orig-")
    cover_path, _, _ = _save_upload(cover, "cov-")

    with original_path.open("rb") as file:
        original_bytes = file.read()

    try:
        stego_bytes = embed_lsb_2bit(
            str(cover_path),
            original_bytes,
            original_ext,
            secret_key,
        )
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 422

    file_id = uuid.uuid4().hex
    output_name = f"stego-{file_id}.png"
    output_path = OUTPUT_DIR / output_name
    output_path.write_bytes(stego_bytes)

    preview = base64.b64encode(stego_bytes).decode("utf-8")

    return jsonify(
        ok=True,
        file_id=file_id,
        download_url=url_for("download_output", file_id=file_id),
        preview=f"data:image/png;base64,{preview}",
    )


@app.post("/api/decrypt")
def api_decrypt():
    stego_file = request.files.get("stego")
    secret_key = (request.form.get("secret_key") or "").strip()

    if not stego_file:
        return jsonify(ok=False, error="Upload 'stego'."), 400

    if not secret_key:
        return jsonify(ok=False, error="Secret key wajib diisi."), 400

    stego_path, _, _ = _save_upload(stego_file, "stego-")

    try:
        original_bytes, extension = extract_lsb_2bit(
            str(stego_path),
            secret_key,
        )
    except ValueError as error:
        return jsonify(ok=False, error=str(error)), 422

    extension = (extension or "png").lower().lstrip(".")
    if f".{extension}" not in ALLOWED_EXTS:
        extension = "bin"

    file_id = uuid.uuid4().hex
    output_name = f"extract-{file_id}.{extension}"
    output_path = OUTPUT_DIR / output_name
    output_path.write_bytes(original_bytes)

    response = {
        "ok": True,
        "download_url": url_for("download_output", file_id=file_id),
    }

    image_extensions = {"png", "jpg", "jpeg", "webp"}
    if extension in image_extensions:
        mime_type = "jpeg" if extension in {"jpg", "jpeg"} else extension
        preview = base64.b64encode(original_bytes).decode("utf-8")
        response["preview"] = f"data:image/{mime_type};base64,{preview}"

    return jsonify(response)


@app.get("/download/<file_id>")
def download_output(file_id: str):
    try:
        uuid.UUID(hex=file_id)
    except (ValueError, AttributeError):
        abort(404)

    matching_files = list(OUTPUT_DIR.glob(f"stego-{file_id}.png"))
    matching_files.extend(OUTPUT_DIR.glob(f"extract-{file_id}.*"))

    if not matching_files:
        abort(404)

    return send_from_directory(
        str(OUTPUT_DIR),
        matching_files[0].name,
        as_attachment=True,
        download_name=matching_files[0].name,
    )


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify(ok=False, error="Ukuran file melebihi batas 25 MB."), 413


@app.errorhandler(415)
def unsupported_file_type(error):
    return jsonify(ok=False, error=error.description or "Tipe file tidak didukung."), 415


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
