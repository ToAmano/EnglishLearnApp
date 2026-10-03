from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    """API向け認証を導入するまではユーザーデータを公開しない。"""
    raise HTTPException(
        status_code=403,
        detail="Use the authenticated Streamlit app. API authentication is not configured.",
    )
