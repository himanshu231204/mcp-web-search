from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    num_results: int = Field(default=5, ge=1, le=20)


class WebSearchResponse(BaseModel):
    results: List[SearchResult]


class FetchPageRequest(BaseModel):
    url: str = Field(..., min_length=1)


class FetchPageResponse(BaseModel):
    title: Optional[str] = None
    content: str
    url: str


class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: dict


class MCPToolsResponse(BaseModel):
    tools: List[MCPTool]


class MCPToolExecutionRequest(BaseModel):
    tool: str = Field(..., description="Tool name to execute")
    input: Dict[str, Any] = Field(..., description="Tool input parameters")
