from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
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
  text: str
  done: bool
  due: datetime.datetime

# TODO auth

@app.get("/todos/{userid}")
async def get_todos(userid: str):
  try:
    # resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("userid").eq(userid))
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
        "text": todo.text,
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

@app.put("/todo/{todoid}")
async def modify_todo(todoid: str, todo: Todo):
  try:
    resp = table.update_item(
      Key={
          "todoid": todoid,
      },
      AttributeUpdates={
        "text": {
          "Value": todo.text,
          "Action": "PUT"
        },
        "done": {
          "Value": todo.done,
          "Action": "PUT"
        },
        "due": {
          "Value": todo.due.isoformat(),
          "Action": "PUT"
        }
      },
      ReturnValues="ALL_NEW"
    )
    return resp["Attributes"]
  except ClientError as err:
    print(err)
    raise HTTPException(500, "error updating todo")
