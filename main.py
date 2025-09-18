import random
from enum import Enum
from typing import Annotated


from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, AfterValidator, BeforeValidator


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})
    return result


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
