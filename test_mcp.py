import asyncio
import httpx
from app.main import app
import uvicorn
import threading
import time

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=10000, log_level="error")

# Start server in background thread
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Wait for server to start
time.sleep(2)

async def test_mcp():
    async with httpx.AsyncClient() as client:
        try:
            print("Testing /mcp endpoint with streaming...")
            # Use a streaming request to see full response
            async with client.stream('GET', 'http://127.0.0.1:10000/mcp', timeout=8.0) as response:
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print()
                
                # Read all chunks
                chunk_count = 0
                async for chunk in response.aiter_text():
                    if chunk:
                        chunk_count += 1
                        print(f"Chunk {chunk_count}:\n{chunk}")
                        if chunk_count >= 3:  # Get first 3 chunks (endpoint + connection_ack + heartbeat)
                            break
                            
                print(f"\nTotal chunks received: {chunk_count}")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

asyncio.run(test_mcp())
