from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from typing import Optional
import boto3
import datetime
import uuid

app = FastAPI()
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("todos_dev")

@app.get("/")
async def root():
  return {"message":"Hello World"}

class Todo(BaseModel):
  userid: str
  todotext: str
  done: bool
  due: datetime.datetime

# TODO auth

@app.get("/todos/{userid}")
async def get_todos(userid: str):
  try:
    resp = table.scan(FilterExpression=boto3.dynamodb.conditions.Attr("userid").eq(userid))
    return resp["Items"]
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error fetching todos")

@app.post("/todo")
async def create_todo(todo: Todo):
  todoid = str(uuid.uuid4())
  try:
    resp = table.put_item(
      Item={
        "todoid": todoid,
        "userid": todo.userid,
        "todotext": todo.todotext,
        "done": todo.done,
        "due": todo.due.isoformat()
      }
    )
    return {"id": todoid}
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error creating todo")

@app.get("/todo/{todoid}")
async def get_todo(todoid: str):
  try:
    todo = table.get_item(Key={"todoid": todoid})
    return todo["Item"]
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error getting todo")

@app.delete("/todo/{todoid}")
async def delete_todo(todoid: str):
  try:
    resp = table.delete_item(Key={"todoid": todoid})
    if resp:
      return {"message": "successfully deleted"}
    else:
      raise HTTPException(500, "error deleting todo")
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error getting todo")

class UpdateTodo(BaseModel):
  userid: str
  todotext: Optional[str]
  done: Optional[bool]
  due: Optional[datetime.datetime]

@app.put("/todo/{todoid}")
async def modify_todo(todoid: str, todo: UpdateTodo):
  my_update_expression = "SET "
  my_expression_attribute_values = {}

  if todo.todotext != None: 
    my_update_expression += "todotext = :valtxt,"
    my_expression_attribute_values[":valtxt"] = todo.todotext
  
  if todo.done != None:
    my_update_expression += "done = :valdone,"
    my_expression_attribute_values[":valdone"] = todo.done
  
  if todo.due != None:
    my_update_expression += "done = :valdue,"
    my_expression_attribute_values[":valdue"] = todo.due
  
  if (todo.todotext == None) & (todo.done != None) & (todo.due != None):
    raise HTTPException(400, "nothing to update")
  
  # cut the last comma
  my_update_expression = my_update_expression[0:-1]

  try:
    resp = table.update_item(
      Key={
          "todoid": todoid,
      },
      UpdateExpression=my_update_expression,
      ExpressionAttributeValues=my_expression_attribute_values,
      ReturnValues="ALL_NEW"
    )
    return resp["Attributes"]
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error updating todo")
