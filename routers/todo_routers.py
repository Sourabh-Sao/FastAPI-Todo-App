from fastapi import FastAPI,HTTPException,status,APIRouter
from sqlmodel import select
from typing import List

from schemas import TodoCreate,TodoRead,TodoUpdate
from database import session_dep
from models import Todo

router = APIRouter()


@router.post("/",response_model=TodoRead)
def create_todo(todo:TodoCreate,session:session_dep):
    db_todo=Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)

    return db_todo


@router.get("/{todo_id}",response_model=TodoRead)
def read_todos(todo_id:int,session:session_dep):
    todo=session.get(Todo,todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo Not Found")
    return todo


@router.get("/",response_model=List[TodoRead])
def read_todo(session:session_dep,offset:int = 0,limit:int=100):
    todos=session.exec(select(Todo).offset(offset).limit(limit)).all()
    return todos


@router.patch("/{todo_id}",response_model=TodoRead)
def update_todo(todo_id:int,todo_data:TodoUpdate,session:session_dep):
    
    # get existing record from db
    db_todo=session.get(Todo,todo_id)

    if not db_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo Not Found")
    
    # why we did model dump reason is below
    update_data=todo_data.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(db_todo,key,value)

    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

@router.delete("/{todo_id}")
def delete_todo(todo_id:int,session:session_dep):
    todo=session.get(Todo,todo_id)

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo Not Found")
    
    session.delete(todo)
    session.commit()
    return {"ok":True,"message":"Deleted Successfully"}

