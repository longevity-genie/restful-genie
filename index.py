#!/usr/bin/env python
import os
from pathlib import Path
from typing import Optional, Union, List
from getpaper.parse import download_and_parse

import loguru
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from langchain.chat_models import ChatOpenAI
from langserve import add_routes
from pycomfort.config import load_environment_keys
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import models

from biotables.web import QueryLLM, SettingsLLM, AskPaper, QueryPaper

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

@app.post("/gpt/", response_model=str)
@cache(expire=expires)
async def ask_gpt(query: QueryLLM):
    llm = default_llm if default_settings.same_settings(query) else query.make_openai_chat()
    result = await llm.ainvoke(query.text)
    #loguru.logger.info("RESPONSE WAS:")
    #loguru.logger.info(result)
    return result.content



@app.post("/ask_paper/", response_model=List[str])
@cache(expire=expires)
async def ask_paper(paper: AskPaper):
    folders: List[Path] = download_and_parse(paper.doi, locations.papers, subfolder=True, do_not_reparse=True)
    if len(folders) <1:
        loguru.logger.error(f"nothing was downloaded/parsed for {paper.doi}")
    loguru.logger.info(f"download folder {paper.doi}")
    return folders


@app.post("/papers/")
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
        if text is None or text is "string":
            results = database.scroll(collection_name=collection_name, scroll_filter=doi_filter, with_payload=query.with_payload, with_vectors=query.with_vectors, limit=query.limit)
        else:
            results = database.query(collection_name=collection_name, query_text=text, query_filter=doi_filter, with_vectors=query.with_vectors, limit=query.limit)
        loguru.logger.info(f"RESULTS RECEIVED:\n")
        end_results = [r.document for r in results]
        loguru.logger.info(f"{end_results}")
        return end_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, timeout_keep_alive=500, ws_ping_timeout= 200, host="0.0.0.0", ws_max_queue = 100, port=int(os.getenv("PORT", 8000)))