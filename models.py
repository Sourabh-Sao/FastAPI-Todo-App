from sqlmodel import SQLModel,Field,Column,func,DateTime
from typing import Optional
from datetime import datetime

class TodoBase(SQLModel):
    title:str=Field(index=True,max_length=500)
    description:Optional[str]=Field(default=None,max_length=500)
    is_complete:bool=Field(default=False)

class Todo(TodoBase,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)

    created_at:datetime=Field(default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )