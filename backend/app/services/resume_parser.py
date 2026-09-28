"""
Resume and Document Parser with magic-byte validation and 25MB upload limit.
Supports PDF, DOCX, and TXT.
"""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",
}


class InvalidFileError(Exception):
    pass


def validate_file(file_bytes: bytes, filename: str) -> str:
    """Validate file extension, size, and magic bytes. Returns detected extension."""
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise InvalidFileError(f"File size {len(file_bytes)} bytes exceeds 25 MB limit.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ["pdf", "docx", "txt"]:
        raise InvalidFileError(f"Unsupported file format: {ext}. Only PDF, DOCX, and TXT are permitted.")

    if ext == "pdf":
        if not file_bytes.startswith(MAGIC_BYTES["pdf"]):
            raise InvalidFileError("File claims to be PDF but lacks PDF magic bytes header.")
    elif ext == "docx":
        if not file_bytes.startswith(MAGIC_BYTES["docx"]):
            raise InvalidFileError("File claims to be DOCX but lacks ZIP/DOCX magic bytes header.")
    elif ext == "txt":
        # Text file validation: ensure it can be decoded as UTF-8 / ASCII
        try:
            file_bytes[:1024].decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidFileError("Text file is not valid UTF-8.")

    return ext


def extract_text_from_bytes(file_bytes: bytes, ext: str) -> str:
    """Extract plain text from file bytes based on extension."""
    if ext == "txt":
        return file_bytes.decode("utf-8", errors="replace")

    elif ext == "pdf":
        import io
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)

    elif ext == "docx":
        import io
        stream = io.BytesIO(file_bytes)
        doc = Document(stream)
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paras)

    raise InvalidFileError(f"Unsupported extension: {ext}")


def extract_text_from_path(file_path: Path) -> str:
    """Extract plain text from an existing file path."""
    with open(file_path, "rb") as f:
        data = f.read()
    ext = file_path.suffix.lstrip(".").lower()
    return extract_text_from_bytes(data, ext)
