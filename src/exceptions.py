from fastapi import HTTPException\

bad_credentials = HTTPException(
    status_code=400,
    detail="Incorrect username or password",
)
unauthorized = HTTPException(
    status_code=401,
    detail='Unauthorized'
)
forbidden = HTTPException(
    status_code=403,
    detail='Access forbidden'
)
not_found = HTTPException(
    status_code=404,
    detail='Not found'
)
internal_error = HTTPException(
    status_code=500,
    detail="Internal server error",
)
