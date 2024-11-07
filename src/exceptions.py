from fastapi import HTTPException


class UserAlreadyExists(Exception): ...
class FetchingError(Exception): ...
class NoSuchUser(Exception): ...
class NoSuchPost(Exception): ...
class NoSuchComment(Exception): ...


bad_credentials = HTTPException(
    status_code=400,
    detail="Incorrect username or password",
)
internal_error = HTTPException(
    status_code=500,
    detail="Internal server error",
)
unauthorized = HTTPException(
    status_code=401,
    detail='Unauthorized'
)
not_found = HTTPException(
    status_code=404,
    detail='Not found'
)
