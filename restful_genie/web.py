from pathlib import Path
from typing import Optional

import loguru
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel
from getpaper.parse import PDFParser

class PaperDownloadRequest(BaseModel):
    doi: str
    selenium_on_fail: bool = False,
    scihub_on_fail: bool = False,
    parser: PDFParser = PDFParser.py_mu_pdf
    subfolder: bool = True
    do_not_reparse: bool = True,
    selenium_min_wait: int = 15,
    selenium_max_wait: int = 60


class QueryPaper(BaseModel):
    doi: Optional[str] = None
    text: Optional[str] = None
    collection_name: str = "bge_base_en_v1.5_aging_5"
    with_vectors: bool = False
    with_payload: bool = True
    db: Optional[str] = None #for opensearch should be URL
    limit: int = 10


class SettingsLLM(BaseModel):
    model_name: str = "gpt-3.5-turbo"
    key: Optional[str] = None
    temperature: float = 0.0
    debug: bool = False

    def make_openai_chat(self) -> ChatOpenAI:
        key_value = None if self.key is None or self.key == "string" else self.key
        return ChatOpenAI(
            model_name = self.model_name,
            temperature = self.temperature,
            openai_api_key = key_value
        )

    def same_settings(self, query: 'QueryLLM') -> bool:
        return self.model_name == query.model_name and self.key == query.key and self.temperature == query.temperature

class QueryLLM(SettingsLLM):
    text: str
    cachable: bool = True #not used yet


class AskPaper(QueryLLM):
    doi: str

    """
    def read(self):
        folders: List[Path] = try_download_and_parse(self.doi, subfolder=True, do_not_reparse=True)
        if len(folders) <1:
            loguru.logger.error(f"nothing was downloaded/parsed for {self.doi}")
        loguru.logger.info(f"download folder {self.doi}")
        return folders
    """
