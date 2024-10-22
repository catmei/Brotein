from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import endpoints

# Create FastAPI app instance
app = FastAPI(debug=True)

# Configure CORS settings to allow the frontend (Flask) to access this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://52.65.239.138:5000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include the router from the endpoints file
app.include_router(endpoints.router)

# Run the app if this file is executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
