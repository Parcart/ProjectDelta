import asyncio
import logging

import uvicorn

from app.db.DAO import DAO
from app.rest.EmailService import EmailService


async def main() -> None:
    DAO()
    EmailService()
    from app.rest.main import app
    uvicorn.run(app, host="0.0.0.0", port=80, reload=False)


if __name__ == "__main__":
    asyncio.run(main())
