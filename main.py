import random
from enum import Enum
from datetime import datetime, time, timedelta
from typing import Annotated, Literal
from uuid import UUID


from fastapi import Body, FastAPI, Path, Query
from pydantic import BaseModel, Field, AfterValidator, BeforeValidator, HttpUrl


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None,
        title="The description of the item",
        max_length=300,
        examples=["priority 3"]
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None
    tags: set[str] = set()
    images: list[Image] | None = None
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "string1",
                    "description": "priority2",
                    "price": 12,
                    "tax": 10,
                    "tags": ["tag1", "tag2"],
                    "images": [
                        {
                            "url": "https://example.com/",
                            "name": "string3"
                        }
                    ]
                },
                {
                    "name": "string11",
                    "description": "string22",
                    "price": 121,
                    "tax": 101,
                    "tags": ["tag11", "tag12"],
                    "images": [
                        {
                            "url": "https://example.com/",
                            "name": "string33"
                        }
                    ]
                },
            ]
        }
    }

class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]


class User(BaseModel):
    username: str
    full_name: str | None = None


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


app = FastAPI()


@app.get("/")
async def root(filter_query: Annotated[FilterParams, Query()]):
    return filter_query


@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images


@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer


data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}


def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id


@app.get("/items/")
async def read_items(
    q: Annotated[
        str | None,
        Query(
            title="Query string", min_length=3, max_length=50, pattern="^fixedquery$"
        ),
    ] = None,
    q2: Annotated[
        list[str],
        Query(
            alias="item-query",
            title="Query string 2",
            description="Query string for the items to search in the database that have a good match",
            min_length=2,
            deprecated=True,
        ),
    ] = ["foo", "bar"],
    id: Annotated[str | None, AfterValidator(check_valid_id)] = None,
    short: Annotated[bool, BeforeValidator(lambda x: x == "true")] = False,
):
    if id:
        item = data.get(id)
    else:
        id, item = random.choice(list(data.items()))
    results = {
        "items": [{"item_id": "Foo"}, {"item_id": "Bar"}],
        "q2": q2,
        "id": id,
        "name": item,
    }
    if q:
        results.update({"q": q})
    return results if not short else {"item_id": "the current item"}


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[UUID, Path(title="The ID of the item to get")],
    importance: Annotated[int, Body(gt=0)],
    item: Annotated[
        Item,
        Body(
            examples=[
                {
                    "name": "Foo",
                    "description": "priority 1",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ],
        ),
    ],
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
    q: str | None = None,
    user: User | None = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    results = {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
    if q:
        results.update({"q": q})
    if item:
        results.update({"item": item})
    if user:
        results.update({"user": user})
    return results


@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1, le=1000)],
    size: Annotated[float, Query(gt=0, lt=10.5)],
    q: Annotated[str | None, Query(alias="item-query")] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return {"user_id": user_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
