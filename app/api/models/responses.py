from fastapi.responses import JSONResponse

def error_response(message: str, status_code: int = 400):
    return JSONResponse(content={"error": message}, status_code=status_code)
