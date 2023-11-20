#!/usr/bin/env python
import os

import loguru
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from getpaper.parse import *
from langchain.chat_models import ChatOpenAI
from langserve import add_routes
from loguru import logger
from pycomfort.config import load_environment_keys
from qdrant_client import QdrantClient
from qdrant_client.http.models import models
from getpaper.download import PaperDownload
from biotables.web import QueryLLM, SettingsLLM, AskPaper, QueryPaper, PaperDownloadRequest

from fastapi.openapi.utils import get_openapi

load_environment_keys(usecwd=True)

from biotables.locations import Locations
locations = Locations(Path("."))

expires = os.getenv("EXPIRES", 3600)
env_db = os.getenv("DATABASE_URL")
loguru.logger.add("logs/biotables.log", rotation="10 MB")
if env_db is None:
    loguru.logger.error(f"URL is none and DATABASE_URL environment variable is not set, using default value instead")
    url = "https://5bea7502-97d4-4876-98af-0cdf8af4bd18.us-east-1-0.aws.cloud.qdrant.io:6333"
else:
    url = env_db

env_key = os.getenv("OPENAI_API_KEY")
env_embed_model= os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

client = QdrantClient(
    url=url,
    port=6333,
    grpc_port=6334,
    prefer_grpc=True,
    api_key=os.getenv("QDRANT_KEY")
)

client.set_model(env_embed_model)


app = FastAPI(
    # Initialize FastAPI cache with in-memory backend
    title="Biotable server",
    version="1.1",
    description="API server to handle queries to biotables",
    debug=True
)

FastAPICache.init(InMemoryBackend())

add_routes(
    app,
    ChatOpenAI(),
    path="/openai"
)


default_settings: SettingsLLM = SettingsLLM(key=env_key)

default_llm = default_settings.make_openai_chat()

@app.post("/gpt/", description="calls chat gpt api, receives QueryLLM with model parameters as input", include_in_schema=False, response_model=str)
@cache(expire=expires)
async def ask_gpt(query: QueryLLM):
    llm = default_llm if default_settings.same_settings(query) else query.make_openai_chat()
    result = await llm.ainvoke(query.text)
    return result.content

@app.post("/download_paper/", description="does downloading and parsing of the model, can optionally fallback to selenium and/or schi-hub for hard to download pdfs", response_model=PaperDownload)
async def parse_pdf_post(request: PaperDownloadRequest):
    #code duplication to check if ChatGPT action can deal with it
    destination = locations.papers
    logger = loguru.logger
    logger.add(sys.stdout)
    downloaded_and_parsed = try_download_and_parse(request.doi, destination, request.selenium_on_fail, request.scihub_on_fail,
                                                   request.parser, request.subfolder, request.do_not_reparse,
                                                   selenium_min_wait=request.selenium_min_wait, selenium_max_wait=request.selenium_max_wait,
                                                   logger=logger) #paper_id, download, metadata
    downloaded_and_parsed.on_failure(lambda e: logger.error(f"issue with {e}"))
    return downloaded_and_parsed.get_or_else_get(lambda ex: PaperDownload(request.doi, None, None))


@app.get("/get_paper/", description="does downloading and parsing of the model, can optionally fallback to selenium and/or schi-hub for hard to download pdfs", response_model=PaperDownload)
async def parse_pdf(doi: str, selenium_on_fail: bool = False, scihub_on_fail: bool = False,
                    parser: PDFParser = PDFParser.py_mu_pdf, subfolder: bool = True, do_not_reparse: bool = True,
                    selenium_min_wait: int = 15, selenium_max_wait: int = 60
                    ):
    destination = locations.papers
    logger = loguru.logger
    logger.add(sys.stdout)
    downloaded_and_parsed = try_download_and_parse(doi, destination, selenium_on_fail, scihub_on_fail,
                                                  parser, subfolder, do_not_reparse,
                                                  selenium_min_wait=selenium_min_wait, selenium_max_wait=selenium_max_wait,
                                                  logger=logger) #paper_id, download, metadata
    downloaded_and_parsed.on_failure(lambda e: logger.error(f"issue with {e}"))
    return downloaded_and_parsed.get_or_else_get(lambda ex: PaperDownload(doi, None, None))


@app.post("/papers/", description="does a search in the vector bases for the papers that fit the query", response_model=List[str])
@cache(expire=expires)
async def get_papers(query: QueryPaper):
    loguru.logger.info(f"executing get papers with {query.text}")
    collection_name = query.collection_name
    text = query.text
    database = client if query.db is None or query.db == env_db else QdrantClient(
        url=url,
        port=6333,
        grpc_port=6334,
        prefer_grpc=True,
        api_key=os.getenv("QDRANT_KEY")
    )
    if "small" not in collection_name:
        database.set_model("BAAI/bge-base-en-v1.5")
    try:
        doi = query.doi
        if doi is not None:
            doi_filter=models.Filter(
                should=[
                    models.FieldCondition(
                        key="doi",
                        match=models.MatchValue(value=doi), #"10.3389/fpsyg.2019.02038"
                    )
                ]
            )
        else:
            doi_filter = None
        if text is None or text == "string":
            results = database.scroll(collection_name=collection_name, scroll_filter=doi_filter, with_payload=query.with_payload, with_vectors=query.with_vectors, limit=query.limit)
        else:
            results = database.query(collection_name=collection_name, query_text=text, query_filter=doi_filter, with_vectors=query.with_vectors, limit=query.limit)
        loguru.logger.info(f"RESULTS RECEIVED:\n")
        end_results = [r.document for r in results]
        loguru.logger.info(f"{end_results}")
        return end_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/version", description="return the version of the current biotables project", response_model=str)
async def version():
    return '0.0.5'


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, timeout_keep_alive=500, ws_ping_timeout= 200, host="0.0.0.0", ws_max_queue = 100, port=int(os.getenv("PORT", 8000)))