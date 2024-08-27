from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class Ticket(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {   
                "name": "Ali",
                "email": "ali@gmail.com",
                "message": "Your web application is awesome :)",
            }
        ]
    })
    name: Annotated[str, Field(max_length=250)]
    email: Annotated[str, Field(max_length=250)]
    message: str
