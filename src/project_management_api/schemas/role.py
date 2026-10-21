from pydantic import BaseModel


class PermissionDetail(BaseModel):
    code: str
    description: str
    roles: list[str]


class RoleDefinition(BaseModel):
    role: str
    scope: str
    description: str
    permissions: list[str]


class RolesResponse(BaseModel):
    roles: list[RoleDefinition]
    permissions: list[PermissionDetail]
