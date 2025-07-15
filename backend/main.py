"""
StudyLink Backend API
Main FastAPI application for the RAG-powered biology study tool.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os

from cnxml_parser import CNXMLParser
from textbook_processor import TextbookProcessor

app = FastAPI(title="StudyLink API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our processors
parser = CNXMLParser()
processor = TextbookProcessor()

class ChatMessage(BaseModel):
    message: str
    context: str = ""

class ChatResponse(BaseModel):
    response: str
    references: List[Dict[str, Any]]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "StudyLink API is running"}

@app.get("/textbook/structure")
async def get_textbook_structure():
    """
    Get the hierarchical structure of the Biology 2e textbook.
    Returns chapters, sections, and modules with navigation info.
    """
    try:
        structure = processor.get_textbook_structure()
        return {"structure": structure}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/textbook/module/{module_id}")
async def get_module_content(module_id: str):
    """
    Get the full content of a specific module by ID.
    Returns parsed text, figures, and metadata.
    """
    try:
        content = processor.get_module_content(module_id)
        if not content:
            raise HTTPException(status_code=404, detail="Module not found")
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_textbook(message: ChatMessage):
    """
    Chat endpoint for asking questions about the textbook.
    Will eventually use RAG to find relevant content and generate responses.
    """
    # TODO: Implement RAG pipeline
    # For now, return a placeholder response
    return ChatResponse(
        response="This is a placeholder response. RAG pipeline coming soon!",
        references=[]
    )

@app.get("/textbook/search")
async def search_textbook(query: str):
    """
    Search through the textbook content.
    Will eventually use vector similarity search.
    """
    # TODO: Implement vector search
    return {"results": [], "query": query}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)