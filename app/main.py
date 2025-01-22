import asyncio
import logging

import uvicorn

from app.db.DAO import DAO
from app.rest.EmailService import EmailService


async def main() -> None:
    await DAO().checkDatabase()
    EmailService()
    from app.rest.main import app
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, reload=False)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
