from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return "This is homepage!"

@app.get("/user")
def getUser():
    return {
        "name" : "Romitha",
        "age" : 21,
        "city" : "Chennai",
        "state" : "Tamilnadu"
    }