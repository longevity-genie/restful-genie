#!/usr/bin/env python
import asyncio
import os
from typing import List, Optional

import loguru
from fastapi import FastAPI, HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langserve import add_routes
from langchain.schema.runnable import RunnableLambda
from pycomfort.config import load_environment_keys
from pydantic import BaseModel
from qdrant_client import QdrantClient, qdrant_client
from qdrant_client.fastembed_common import QueryResponse
from qdrant_client.http.models import models

load_environment_keys(usecwd=True)
env_db = os.getenv("DATABASE_URL")
if env_db is None:
    loguru.logger.error(f"URL is none and DATABASE_URL environment variable is not set, using default value instead")
    url = "https://5bea7502-97d4-4876-98af-0cdf8af4bd18.us-east-1-0.aws.cloud.qdrant.io:6333"
else:
    url = env_db

env_key = os.getenv("OPENAI_API_KEY")

client = QdrantClient(
    url=url,
    port=6333,
    grpc_port=6334,
    prefer_grpc=True,
    api_key=os.getenv("QDRANT_KEY")
)
client.set_model("BAAI/bge-base-en-v1.5")

app = FastAPI(
    title="Biotable server",
    version="1.0",
    description="API server to handle",
)

add_routes(
    app,
    ChatOpenAI(),
    path="/openai"
)

class SettingsLLM(BaseModel):
    model_name: str = "gpt-3.5-turbo"
    key: Optional[str] = None
    temperature: float = 0.0

    def same_settings(self, query: 'QueryLLM') -> bool:
        return self.model_name == query.model_name and self.key == query.key and self.temperature == query.temperature

class QueryLLM(SettingsLLM):
    text: str

def make_llm(query: QueryLLM) -> ChatOpenAI:
    return ChatOpenAI(
        model_name = query.model_name,
        temperature = query.temperature,
        openai_api_key = query.key
    )


default_settings: SettingsLLM = SettingsLLM(key=env_key)

default_llm = make_llm(default_settings)

@app.post("/gpt/", response_model=str)
async def get_papers(query: QueryLLM):
    llm = default_llm if default_settings.same_settings(query) else make_llm(query)
    result = llm.invoke(query.text)
    return result.content


class QueryPaper(BaseModel):
    doi: Optional[str] = None
    text: Optional[str] = None
    collection_name: str = "bge_base_en_v1.5_aging_5"
    with_vectors: bool = False
    with_payload: bool = True
    db: Optional[str] = None
    limit: int = 1

@app.post("/papers/")
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
        if text is None:
            results = database.scroll(collection_name=collection_name, scroll_filter=doi_filter, with_payload=query.with_payload, with_vectors=query.with_vectors, limit=query.limit)
        else:
            results = database.query(collection_name=collection_name, query_text=text, query_filter=doi_filter, with_vectors=query.with_vectors, limit=query.limit)
        loguru.logger.info(f"RESULTS RECEIVED:\n")
        loguru.logger.info(f"{results[0].document}")
        return [] if len(results) < 1 else results[0].document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    loguru.logger.info("INFO")
    #results = asyncio.run(get_papers(QueryPaper(doi = "10.3389/fpsyg.2019.02038", db = env_db)))
    #loguru.logger.info(results)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))