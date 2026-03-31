from fastapi import FastAPI

from database import create_db_and_table
from routers import todo_routers


app = FastAPI(title="Smart Task Manager")


@app.on_event("startup")
def on_startup():
    create_db_and_table()

# Router ko app ke saath jodein
# prefix="/todos" ka matlab hai ki saare urls automatic /todos/ se start honge
app.include_router(todo_routers.router, prefix="/todos", tags=["Tasks"])