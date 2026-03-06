"""Shared application state for FastAPI routers."""
from typing import Optional

from etl.extractor import Extractor
from etl.load import Load

extractor: Optional[Extractor] = None
load: Optional[Load] = None
