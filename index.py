#!/usr/bin/env python
import os
from typing import List

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from getpaper.parse import *
from fastapi.openapi.models import ExternalDocumentation
from hybrid_search.opensearch_hybrid_search import OpenSearchHybridSearch
from langchain.embeddings import HuggingFaceBgeEmbeddings
from pycomfort.config import load_environment_keys
from qdrant_client import QdrantClient
from qdrant_client.fastembed_common import QueryResponse
from qdrant_client.http.models import models
from starlette.middleware.cors import CORSMiddleware
from hybrid_search.opensearch_hybrid_search import *

from restful_genie.web import QueryLLM, SettingsLLM, QueryPaper, PaperDownloadRequest

load_environment_keys(usecwd=True)

from restful_genie.locations import Locations
locations = Locations(Path("."))

expires = os.getenv("EXPIRES", 3600)
env_db = os.getenv("DATABASE_URL")
loguru.logger.add("logs/restful_genie.log", rotation="10 MB")
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
    title="Restful longevity genie server",
    version="1.1",
    description="API server to handle queries to restful_genie",
    debug=True
)

FastAPICache.init(InMemoryBackend())

"""
# we do not really need langserve stuff right noww
from langserve import add_routes
add_routes(
    app,
    ChatOpenAI(),
    path="/openai"
)
"""


default_settings: SettingsLLM = SettingsLLM(key=env_key)

default_llm = default_settings.make_openai_chat()

device: str = "cpu"
embeddings_model_name = "BAAI/bge-base-en-v1.5"
model_kwargs = {"device": device}
encode_kwargs = {"normalize_embeddings": True}

embeddings = HuggingFaceBgeEmbeddings(
    model_name=embeddings_model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)



@app.post("/gpt/", description="calls chat gpt api, receives QueryLLM with model parameters as input", include_in_schema=False, response_model=str)
@cache(expire=expires)
async def ask_gpt(query: QueryLLM):
    llm = default_llm if default_settings.same_settings(query) else query.make_openai_chat()
    result = await llm.ainvoke(query.text)
    return result.content


@app.post("/download_paper/", description="does downloading and parsing of the model, can optionally fallback to selenium and/or schi-hub for hard to download pdfs", response_model=PaperDownload)
@cache(expire=expires)
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

@app.post("/hybrid_search/", description="does hybrid search in the literature, provides sources together with answers", response_model=List[str])
@cache(expire=expires)
async def hybrid_search(query: QueryPaper):
    loguru.logger.info(f"HYBRID SEARCH ON: '{query.text}'")

    collection_name = query.collection_name
    text = query.text
    k = query.limit
    url = query.db if query.db is not None else os.getenv("OPENSEARCH_URL", "https://localhost:9200")
    docsearch = OpenSearchHybridSearch.create(url, collection_name, embeddings)
    print(f"url={url}, index={collection_name}, query={text}")
    results: list[Document] = docsearch.similarity_search(text, k=k, search_type = HYBRID_SEARCH, search_pipeline = "norm-pipeline")
    print(results)
    #loguru.logger.trace(f"RESULTS RECEIVED:\n {results}")
    loguru.logger.info(f"RESULTS RECEIVED:\n {results}")
    def document_to_string(d: Document)-> str:
        return f"{d.page_content} SOURCE: {'http://doi.org/'+d.metadata['doi'] if 'doi' in d.metadata and d.metadata['doi'] is not None else d.metadata['source']}"
    return [document_to_string(d) for d in results]


@app.post("/semantic_search/", description="does semantic search in the literature, provides sources together with answers", response_model=List[str])
@cache(expire=expires)
async def semantic_search(query: QueryPaper):
    loguru.logger.info(f"SEMANTIC SEARCH ON: '{query.text}'")
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
            end_results = [r.document for r in results]
            loguru.logger.trace(f"RESULTS RECEIVED:\n {end_results}")
            return end_results
        else:
            def query_to_answer(q: QueryResponse)-> str:
                return f"{q.document} SOURCE: {'http://doi.org/'+q.metadata['doi'] if 'doi' in q.metadata and q.metadata['doi'] is not None else q.metadata['source']}"
            results: list[QueryResponse] = database.query(collection_name=collection_name, query_text=text, query_filter=doi_filter, with_vectors=query.with_vectors, limit=query.limit)
            end_results = [query_to_answer(r) for r in results]
            loguru.logger.trace(f"RESULTS RECEIVED:\n {end_results}")
            return end_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/privacy-policy")
async def privacy_policy():
    return FileResponse('privacy_policy.md')

@app.get("/terms")
async def terms_of_service():
    return FileResponse('terms_of_service.md')

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Longevity Genie and restful_genie REST API",
        version="0.0.11",
        description="This REST service provides means for semantic search in scientific literature and downloading papers. [Privacy Policy](http://yourapp.com/privacy-policy).",
        terms_of_service="https://agingkills.eu/terms/",
        routes=app.routes,
    )
    if Path("agingkills.eu.key").exists():
        openapi_schema["servers"] = [{"url": "https://agingkills.eu"}, {"url": "http://localhost:8000"}]
        openapi_schema["externalDocs"] = ExternalDocumentation(
            description="Privacy Policy",
            url="https://agingkills.eu/privacy-policy"
        ).dict()
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.openapi = custom_openapi

@app.get("/version", description="return the version of the current restful_genie project", response_model=str)
async def version():
    return '0.0.11'


if __name__ == "__main__":
    import uvicorn

    # Define the paths for SSL certificate files using pathlib
    ssl_keyfile = Path("agingkills.eu.key")
    ssl_certfile = Path("Certificate.pem")

    if ssl_keyfile.exists() and ssl_certfile.exists():
        # SSL certificates are available, run with HTTPS
        uvicorn.run(app,
                    host="0.0.0.0",
                    port = int(os.getenv("PORT", 443)),
                    ssl_keyfile=str(ssl_keyfile),
                    ssl_certfile=str(ssl_certfile)
                    )
    else:
        # SSL certificates are not available, run without HTTPS
        uvicorn.run(app,
                    host="0.0.0.0",
                    port=int(os.getenv("PORT", 8000)))
