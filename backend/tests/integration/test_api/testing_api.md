# Start the server
cd backend
source venv/bin/activate
uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/
curl http://localhost:8000/api/v1/health

# Access documentation
# Open browser: http://localhost:8000/docs