"""Document parsers — full implementation.

Supports PDF, DOCX, TXT, Markdown, and CSV. Each parser produces a
:class:`ParsedDocument` containing a list of :class:`ParsedPage` objects
that preserve page numbers and heading-derived sections.
"""
from __future__ import annotations

import csv
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import structlog

log = structlog.get_logger(__name__)


# --------------------------------------------------------------------------- #
# Data-classes
# --------------------------------------------------------------------------- #


@dataclass
class ParsedPage:
    """A single logical page or section extracted from a document."""

    page_number: int
    text: str
    section: Optional[str] = None


@dataclass
class ParsedDocument:
    """The result of parsing an entire document."""

    pages: List[ParsedPage] = field(default_factory=list)
    num_pages: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _clean_text(text: str) -> str:
    """Remove null bytes, normalize unicode, collapse whitespace."""
    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFKC", text)
    # Collapse runs of spaces/tabs on a single line, but keep newlines
    text = re.sub(r"[ \t]+", " ", text)
    # Remove lines that are only whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# Parser implementations
# --------------------------------------------------------------------------- #


class DocumentParser:
    """Dispatches to the correct parser based on file extension."""

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def parse(self, file_path: str) -> ParsedDocument:
        """Auto-detect file type and parse the document."""
        ext = Path(file_path).suffix.lower().lstrip(".")
        dispatch = {
            "pdf": self.parse_pdf,
            "docx": self.parse_docx,
            "txt": self.parse_txt,
            "md": self.parse_markdown,
            "markdown": self.parse_markdown,
            "csv": self.parse_csv,
        }
        parser_fn = dispatch.get(ext)
        if parser_fn is None:
            raise ValueError(f"Unsupported file type: '.{ext}'")
        log.info("parser.dispatch", file=file_path, ext=ext)
        return parser_fn(file_path)

    # ---------------------------------------------------------------------- #
    # PDF
    # ---------------------------------------------------------------------- #

    def parse_pdf(self, file_path: str) -> ParsedDocument:
        """Extract text per page using PyPDF2."""
        import PyPDF2  # noqa: PLC0415

        pages: List[ParsedPage] = []
        with open(file_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            for page_num, page in enumerate(reader.pages, start=1):
                raw = page.extract_text() or ""
                text = _clean_text(raw)
                if text:
                    pages.append(ParsedPage(page_number=page_num, text=text))

        return ParsedDocument(
            pages=pages,
            num_pages=len(pages),
            metadata={"source": os.path.basename(file_path), "file_type": "pdf"},
        )

    # ---------------------------------------------------------------------- #
    # DOCX
    # ---------------------------------------------------------------------- #

    def parse_docx(self, file_path: str) -> ParsedDocument:
        """Extract paragraphs from a DOCX file; detect headings as sections."""
        from docx import Document as DocxDocument  # noqa: PLC0415

        doc = DocxDocument(file_path)
        pages: List[ParsedPage] = []
        current_section: Optional[str] = None
        buffer: List[str] = []
        page_num = 1

        for para in doc.paragraphs:
            style_name = para.style.name if para.style else ""
            text = _clean_text(para.text)
            if not text:
                continue

            is_heading = style_name.lower().startswith("heading")
            if is_heading:
                # Flush current buffer as a page
                if buffer:
                    pages.append(
                        ParsedPage(
                            page_number=page_num,
                            text="\n".join(buffer),
                            section=current_section,
                        )
                    )
                    page_num += 1
                    buffer = []
                current_section = text
            else:
                buffer.append(text)

        # Flush remaining content
        if buffer:
            pages.append(
                ParsedPage(
                    page_number=page_num,
                    text="\n".join(buffer),
                    section=current_section,
                )
            )

        return ParsedDocument(
            pages=pages,
            num_pages=len(pages),
            metadata={"source": os.path.basename(file_path), "file_type": "docx"},
        )

    # ---------------------------------------------------------------------- #
    # Plain text
    # ---------------------------------------------------------------------- #

    def parse_txt(self, file_path: str) -> ParsedDocument:
        """Read a plain text file as a single page."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        text = _clean_text(raw)
        pages = [ParsedPage(page_number=1, text=text)] if text else []
        return ParsedDocument(
            pages=pages,
            num_pages=len(pages),
            metadata={"source": os.path.basename(file_path), "file_type": "txt"},
        )

    # ---------------------------------------------------------------------- #
    # Markdown
    # ---------------------------------------------------------------------- #

    def parse_markdown(self, file_path: str) -> ParsedDocument:
        """Parse Markdown, splitting on headings to derive sections."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()

        pages: List[ParsedPage] = []
        current_section: Optional[str] = None
        buffer: List[str] = []
        page_num = 1

        for line in raw.splitlines():
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                if buffer:
                    text = _clean_text("\n".join(buffer))
                    if text:
                        pages.append(
                            ParsedPage(
                                page_number=page_num,
                                text=text,
                                section=current_section,
                            )
                        )
                        page_num += 1
                    buffer = []
                current_section = heading_match.group(2).strip()
            else:
                buffer.append(line)

        if buffer:
            text = _clean_text("\n".join(buffer))
            if text:
                pages.append(
                    ParsedPage(
                        page_number=page_num,
                        text=text,
                        section=current_section,
                    )
                )

        return ParsedDocument(
            pages=pages,
            num_pages=len(pages),
            metadata={"source": os.path.basename(file_path), "file_type": "md"},
        )

    # ---------------------------------------------------------------------- #
    # CSV
    # ---------------------------------------------------------------------- #

    def parse_csv(self, file_path: str) -> ParsedDocument:
        """Convert CSV rows to human-readable text chunks (one page per row)."""
        pages: List[ParsedPage] = []
        with open(file_path, "r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            for page_num, row in enumerate(reader, start=1):
                parts = [f"{k}: {v}" for k, v in row.items() if v is not None]
                text = _clean_text(", ".join(parts))
                if text:
                    pages.append(ParsedPage(page_number=page_num, text=text))

        return ParsedDocument(
            pages=pages,
            num_pages=len(pages),
            metadata={
                "source": os.path.basename(file_path),
                "file_type": "csv",
                "columns": ", ".join(headers),
            },
        )
