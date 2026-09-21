import fitz  # PyMuPDF
import uuid
from pathlib import Path
from typing import List, Tuple
from src.ingestion.schema import (
    DocumentParseResult,
    ParsedElement,
    ElementType,
    TableData,
    ParseConfidence,
)


class LayoutAwareLoader:
    def __init__(self, empty_cell_ratio_threshold: float = 0.45):
        self.empty_cell_ratio_threshold = empty_cell_ratio_threshold

    def _validate_table(self, headers: List[str], rows: List[List[str]]) -> Tuple[bool, List[str]]:
        """
        Catches Case B: Verifies table integrity.
        Flags collapsed columns, wild row variances, or excessive empty cells.
        """
        flags = []
        if not rows:
            flags.append("table_has_no_rows")
            return False, flags

        expected_cols = len(headers) if headers else len(rows[0])
        if expected_cols == 0:
            flags.append("table_zero_columns")
            return False, flags

        total_cells = 0
        empty_cells = 0

        for idx, row in enumerate(rows):
            total_cells += len(row)
            empty_cells += sum(1 for cell in row if not cell or cell.strip() == "")

            # Check column count drift per row
            if len(row) != expected_cols:
                flags.append(f"row_{idx}_col_drift_{len(row)}_vs_{expected_cols}")

        empty_ratio = empty_cells / total_cells if total_cells > 0 else 1.0
        if empty_ratio > self.empty_cell_ratio_threshold:
            flags.append(f"high_empty_cell_ratio_{empty_ratio:.2f}")

        is_valid = len(flags) == 0
        return is_valid, flags

    def load_pdf(self, file_path: str | Path) -> DocumentParseResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Target document not found: {path}")

        doc = fitz.open(path)
        parsed_elements: List[ParsedElement] = []
        all_flags: List[str] = []
        table_count = 0
        doc_id = str(uuid.uuid4())

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Step 1: Detect and extract tables using PyMuPDF's table finder
            tabs = page.find_tables()
            table_bboxes = []

            for tab in tabs:
                table_count += 1
                headers = [str(h) if h is not None else "" for h in (tab.header.names or [])]
                extracted_rows = []
                
                for row in tab.extract():
                    extracted_rows.append([str(c) if c is not None else "" for c in row])

                is_valid, validation_flags = self._validate_table(headers, extracted_rows)
                if not is_valid:
                    all_flags.extend([f"p{page_num+1}_table{table_count}:{flag}" for flag in validation_flags])

                table_data = TableData(
                    headers=headers,
                    rows=extracted_rows,
                    row_count=len(extracted_rows),
                    col_count=len(headers) if headers else (len(extracted_rows[0]) if extracted_rows else 0),
                )

                # Store both the structured representation and the text representation
                table_text = "\n".join([" | ".join(row) for row in extracted_rows])

                parsed_elements.append(
                    ParsedElement(
                        element_id=f"{doc_id}_p{page_num+1}_t{table_count}",
                        element_type=ElementType.TABLE,
                        text=table_text,
                        metadata={"page": page_num + 1, "is_valid": is_valid},
                        table_data=table_data,
                    )
                )
                table_bboxes.append(tab.bbox)

            # Step 2: Extract text outside of table bounding boxes
            # (Ensures table content isn't duplicated as narrative text)
            blocks = page.get_text("blocks")
            for b in blocks:
                # b = (x0, y0, x1, y1, text, block_no, block_type)
                bbox = fitz.Rect(b[:4])
                text = b[4].strip()
                if not text:
                    continue

                # Ignore block if it falls within any detected table
                in_table = any(bbox.intersects(fitz.Rect(tbox)) for tbox in table_bboxes)
                if in_table:
                    continue

                # Basic heuristic: short, capitalized, or numbered lines treated as headers
                elem_type = ElementType.NARRATIVE
                lines = text.splitlines()
                if len(lines) == 1 and (len(text) < 80 or text.isupper() or text.strip().startswith(("Section", "RG", "CPS"))):
                    elem_type = ElementType.HEADER

                parsed_elements.append(
                    ParsedElement(
                        element_id=f"{doc_id}_p{page_num+1}_b{b[5]}",
                        element_type=elem_type,
                        text=text,
                        metadata={"page": page_num + 1},
                    )
                )

        doc.close()

        confidence = ParseConfidence.HIGH if len(all_flags) == 0 else ParseConfidence.LOW

        return DocumentParseResult(
            document_id=doc_id,
            file_name=path.name,
            elements=parsed_elements,
            confidence=confidence,
            flags=all_flags,
            total_tables=table_count,
            total_elements=len(parsed_elements),
        )