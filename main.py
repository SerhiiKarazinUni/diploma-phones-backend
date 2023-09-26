from fastapi import FastAPI, Query, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import time

app = FastAPI()

origins = ["http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix_tree: AsyncIOMotorCollection
documents: AsyncIOMotorCollection


async def unwind(root: AsyncIOMotorCollection, q: List[str], depth: int, used_children: List[str]):
    global prefix_tree, documents
    result = []
    if depth >= len(q) and len(root['documents']) > 0:
        for doc in root['documents']:
            result.append(doc)
    for child in root['children']:
        child_obj = await prefix_tree.find_one({'_id': child})
        if child_obj is None:
            continue
        if depth < len(q) and q[depth] != child_obj['hash']:
            continue
        else:
            used_children.append(str(child_obj['_id']))
            result.extend(await unwind(child_obj, q, depth + 1, used_children))
    return result


# API implementation

@app.on_event("startup")
async def start_db():
    global prefix_tree, documents
    client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = client["diploma_phones"]
    prefix_tree = db["prefix_tree"]
    documents = db["documents"]


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    if request.method != 'OPTIONS' and ('X-Secret' not in request.headers or request.headers['X-Secret'] != 'secret API token'):
        response = Response()
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/search")
async def search(q: List[str] = Query(max_length=50), response: Response = None):
    global prefix_tree, documents

    # prevent from empty or too short search queries
    if q is None or len(q) == 1 or len(q) > 14:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return {}

    #
    used_children = []

    # there may be more than one root
    roots = await prefix_tree.find({'hash': q[0]}).to_list(100)

    result_ids = []
    for root in roots:
        if len(root['children']) == 0:
            continue
        try:
            result_ids.extend(await unwind(root, q, 1, used_children))
            used_children.insert(0, str(root['_id']))
        except Exception as e:
            continue

    # get unique IDs and load corresponding documents
    result_ids = list(set(result_ids))
    docs = await documents.find({'_id': {'$in': result_ids}}).to_list(100)

    response_data = []

    for doc in docs:
        response_data.append({
            'id': str(doc['_id']),
            'phone': doc['phone']
        })

    if len(response_data) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

    return {
        '_used_children': used_children,
        'records': response_data
    }
