from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.favorite import get_favorites_words

app = FastAPI()

# CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # In production, you should restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/favorites", response_model=List[str])
def read_favorites() -> List[str]:
    """
    Endpoint to get the list of favorite words.
    """
    favorites: List[str] = get_favorites_words()
    return favorites


# To run this API, use the following command in your terminal:
# uvicorn src.api:app --reload
