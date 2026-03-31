from sqlmodel import SQLModel,Field,func,Column,DateTime
from typing import Optional
from datetime import datetime,timezone

from models import TodoBase

class TodoCreate(TodoBase):
    pass

class TodoRead(TodoBase):
    id:int
    created_at:datetime


class TodoUpdate(SQLModel):
    title:Optional[str]=Field(default=None,max_length=500)
    description:Optional[str]=Field(default=None,max_length=500)
    is_complete:Optional[bool]=None
