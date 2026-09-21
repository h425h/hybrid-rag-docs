from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ElementType(str, Enum):
    TITLE = "Title"
    HEADER = "Header"
    NARRATIVE = "NarrativeText"
    LIST_ITEM = "ListItem"
    TABLE = "Table"
    UNCATEGORIZED = "Uncategorized"


class ParseConfidence(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"
    FAILED = "FAILED"


class TableData(BaseModel):
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    raw_html: Optional[str] = None
    row_count: int = 0
    col_count: int = 0


class ParsedElement(BaseModel):
    element_id: str
    element_type: ElementType
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    table_data: Optional[TableData] = None


class DocumentParseResult(BaseModel):
    document_id: str
    file_name: str
    elements: List[ParsedElement]
    confidence: ParseConfidence
    flags: List[str] = Field(default_factory=list)
    total_tables: int = 0
    total_elements: int = 0