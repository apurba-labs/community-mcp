from pydantic import BaseModel, Field


class MyBatchContext(BaseModel):
    batch_year: int = Field(ge=1900, le=2100)
    registered_alumni_count: int = Field(ge=0)
