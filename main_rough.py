from fastapi import FastAPI,HTTPException,Depends,status

from sqlmodel import SQLModel,Field,Column,DateTime,func,create_engine,Session,select
from typing import Optional,Annotated,List

from datetime import datetime,timezone

#!---------------------------------------------- 
# 1. Base Logic
class TodoBase(SQLModel):
    title:str=Field(index=True,max_length=500)
    description:Optional[str]=Field(default=None,max_length=500)
    is_complete:bool=Field(default=False)

# 2. Data In : What API receives
class TodoCreate(TodoBase):
    pass

# 3. Data Out: What the API returns (Includes ID)
# TodoRead mein id: int hai kyunki ye sirf ek blueprint hai jo FastAPI ko batata hai ki "Bhai, jab output bhejo toh usme id zaroor hona chahiye."

class TodoRead(TodoBase):
    id:int
    created_at:datetime

# Todo mein id ke saath table=True aur primary_key=True hai. Ye database ko order deta hai ki "Ek column banao jo auto-increment ho."

class Todo(TodoBase,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)

    # this line mean python will create datetime
    # created_at:datetime=Field(
    #     default_factory=lambda:datetime.now(timezone.utc)
    # )

    # this line mean databse will create datetime
    #* Server-side timestamp (Database handles it)
    created_at:datetime=Field(default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


#? update model

class TodoUpdate(SQLModel):
    title:Optional[str]=Field(default=None,max_length=500)
    description:Optional[str]=Field(default=None,max_length=500)
    is_complete:Optional[bool]=None



sqlite_file_name="todo_database.db"
sqlite_url=f"sqlite:///{sqlite_file_name}"

# engine creation
engine=create_engine(sqlite_url,echo=True)

# creating database and table
def create_db_and_table():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        # yield ka use isliye hota hai taaki har naye user ko ek fresh aur saaf session mile, aur kaam hote hi wo band ho jaye.
        yield session


session_dep=Annotated[Session,Depends(get_session)]

# fastAPI part

app=FastAPI(title="Smart Task Manager")

#* Ye code isliye likhte hain taaki server start hote hi aapka Database aur Tables apne aap taiyar ho jayein, aur aapko manually kuch na karna pade.
#* "startup" yahan ek Special Keyword (yaani ek signal) hai jo FastAPI ko batata hai ki ye function kab chalana hai.
@app.on_event("startup")
def on_startup():
    create_db_and_table()

# 1. Creating todo
# response_model isliye hai taaki aap user ko bata sako: "Bhai, tera task mil gaya hai, aur Database ne ise ye ID (Birth Certificate) di hai."
@app.post("/todos/",response_model=TodoRead)
def create_todo(todo:TodoCreate,session:session_dep):

    # Haan, aapne sahi kaha! model_validate TodoCreate se data leta hai, use Todo ke blueprint se match/compare karta hai, aur phir ek aisa object banata hai jise Database bina kisi error ke accept kar le.
    db_todo=Todo.model_validate(todo)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)

    return db_todo

# 2. Read one todo
@app.get("/todos/{todo_id}",response_model=TodoRead)
def read_todos(todo_id:int,session:session_dep):
    todo=session.get(Todo,todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo Not Found")
    return todo

# 3. get all 
@app.get("/todos/",response_model=List[TodoRead])
def read_todo(session:session_dep,offset:int = 0,limit:int=100):
    todos=session.exec(select(Todo).offset(offset).limit(limit)).all()
    return todos


@app.patch("/todos/{todo_id}",response_model=TodoRead)
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

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id:int,session:session_dep):
    todo=session.get(Todo,todo_id)

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo Not Found")
    
    session.delete(todo)
    session.commit()
    return {"ok":True,"message":"Deleted Successfully"}


#! Learning
#* default vs default_factory
# ----------------------------------------------
#? Jab aapko pata ho ki har naye item ki value hamesha ek hi fixed cheez hogi, toh aap default use karte hain. 

#? Jab aap chahte hain ki har naye item ki value alag ho ya usi waqt calculate ho jab data create ho raha ho, toh default_factory use hota hai.

# ----------------------------------------------
#* yield
# Iska simple logic:
# return session ko bhej kar darwaza band kar deta hai (jisse error aayega).

# yield session ko bhejta hai lekin darwaza khula rakhta hai, taaki jab API ka kaam khatam ho jaye, toh wo wapis aakar connection ko sahi se clean/close kar sake.

# Agar aap yield use nahi karenge, toh production mein aapke database ke connections "open" reh jayenge aur server crash ho jayega.

#? ----------------------------------------------
#* Dependency Injection vs No dependency Injection
#! No DI
# Ganda Code (Hardcoded - No DI):

# Python
# @app.post("/todo")
# def create():
#     # Route khud mehnat kar raha hai
#     engine = create_engine("sqlite:///db.sqlite")
#     session = Session(engine)
#     # ... logic ...
#     session.close() # Ye bhool gaye toh khatra!

#* with DI
# @app.post("/todo")
# def create(todo: TodoCreate, session: session_dep):
#     # Route ko bana-banaya session mila
#     new_todo = Todo.model_validate(todo)
#     session.add(new_todo)
#     session.commit()
#     return new_todo
    # Session apne aap band ho jayega!
#? ----------------------------------------------

#* model_dump
# model_dump(exclude_unset=True) isliye karte hain taaki:
# Data Dictionary ban jaye (jo loop chalane ke liye zaroori hai).
# Sirf wahi fields update hon jo user ne bheji hain.

# 1. model_dump(exclude_unset=True) ka asli kaam
# Maan lijiye aapka Todo aisa dikhta hai:

# title: "Gym jaana"

# description: "Subah 6 baje"

# is_complete: False

# Ab user sirf is_complete ko True karna chahta hai. Wo baaki cheezein nahi bhej raha.

# Agar aap model_dump() nahi karte: Pydantic apne default values use kar lega (jaise title ko None kar dega), aur aapka purana data ud jayega.

# exclude_unset=True ka kamaal: Ye sirf wahi fields nikalta hai jo user ne asliyat mein bheji hain. Agar user ne sirf is_complete bheja, toh update_data mein sirf ek hi cheez aayegi: {"is_complete": True}.