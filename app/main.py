from fastapi import FastAPI, HTTPException
from api.contacts import router as contacts_router
from api.authentication import router as auth_router
from api.users import router as users_router
from errors import ContactNotFoundError

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from schemas import ErrorContent, ErrorsContent
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Contacts App")

origins = [
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")

@app.exception_handler(ContactNotFoundError)
def item_not_found_error_handler(request: Request, exc: ContactNotFoundError):
    error = ErrorContent(message=str(exc))
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorsContent(errors=[error]).model_dump(),
    )


@app.exception_handler(ValueError)
def item_not_found_error_handler(request: Request, exc: ValueError):
    error = ErrorContent(message=str(exc))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorsContent(errors=[error]).model_dump(),
    )


@app.exception_handler(HTTPException)
def http_exception_error_handler(request: Request, exc: HTTPException):
    error = ErrorContent(message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code, content=ErrorsContent(errors=[error]).model_dump()
    )


def handle_validation(validation_error) -> ErrorContent:
    message = f"{validation_error['msg']} '{'.'.join(validation_error['loc'][1:])}'"
    return ErrorContent(message=message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [handle_validation(err) for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorsContent(errors=errors).model_dump(),
    )


@app.exception_handler(Exception)
def item_not_found_error_handler(request: Request, exc: Exception):
    error = ErrorContent(message=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorsContent(errors=[error]).model_dump(),
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    error = ErrorContent(message=str(f"Request limit exceeded for {request.client.host}. Please try again later."))
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ErrorsContent(errors=[error]).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
