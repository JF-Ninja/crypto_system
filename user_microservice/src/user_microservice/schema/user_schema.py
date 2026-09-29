from pydantic import BaseModel


class SUserBase(BaseModel):
    email: str

class SUserRegister(SUserBase):
    password: str

class UserIsActive(BaseModel):
    is_active: bool

class SUserUpdate(BaseModel):
    password: str | None
