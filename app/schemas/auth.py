from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(
        default="user@example.com",
        min_length=1,
        description="User email used as login.",
        examples=["user@example.com"],
    )
    password: str = Field(
        default="user12345",
        min_length=1,
        description="Plain password for the user account.",
        examples=["user12345"],
    )


class TokenResponse(BaseModel):
    access_token: str = Field(
        description="JWT access token for Bearer authentication.",
        examples=["jwt-token"],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type used in the Authorization header.",
        examples=["bearer"],
    )


class AdminCheckResponse(BaseModel):
    user_id: int = Field(
        description="Authenticated user identifier.",
        examples=[1],
    )
    email: str = Field(
        description="Authenticated user email.",
        examples=["user@example.com"],
    )
    is_admin: bool = Field(
        description="Whether the authenticated user has administrator privileges.",
        examples=[False],
    )
