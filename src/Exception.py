from fastapi import HTTPException
from fastapi.responses import JSONResponse
import warnings
from src.Schemas import TaskResponse
from typing import Callable, Any
from functools import wraps
import traceback


def handle_exceptions(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> JSONResponse:
        try:
            return func(*args, **kwargs)

        except HTTPException as http_exc:
            traceback_str = "".join(
                traceback.format_exception(None, http_exc, http_exc.__traceback__)
            )
            task_response = TaskResponse()
            task_response.error = "HTTP Exception"
            task_response.error_data = http_exc.detail

            warnings.warn(traceback_str)
            return JSONResponse(
                content=task_response.model_dump(), status_code=http_exc.status_code
            )

        except Exception as exc:
            traceback_str = "".join(
                traceback.format_exception(None, exc, exc.__traceback__)
            )
            try:
                error, error_data = exc.args
            except:
                error_data = str(exc.args)
                error = "Internal Error"
            task_response = TaskResponse()
            task_response.error = error
            task_response.error_data = error_data

            warnings.warn(str(traceback_str))
            return JSONResponse(content=task_response.model_dump(), status_code=500)

    return wrapper
