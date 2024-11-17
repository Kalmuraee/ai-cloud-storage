from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class BucketBase(BaseModel):
    name: str


class BucketCreate(BucketBase):
    pass


class Bucket(BucketBase):
    creation_date: datetime

    class Config:
        from_attributes = True


class ObjectInfo(BaseModel):
    bucket_name: str
    object_name: str
    size: int
    last_modified: datetime
    etag: Optional[str] = None
    content_type: Optional[str] = None

    class Config:
        from_attributes = True


class ObjectList(BaseModel):
    objects: List[ObjectInfo]