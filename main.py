"""
This file is used to launch modules and initialize the application
"""
import argparse
import asyncio


def run_fastapi():
    """
    Run Rest API and initialize of objects necessary for work
    """
    # DAO()
    # EmailService()
    # uvicorn.run(app, host="0.0.0.0", port=80, reload=False)


async def run_rpc():
    """
    Run RPC and initialize of objects necessary for work
    :return:
    """
    # from api.rpc.main import serve
    # from bot.Bot import Bot
    # Bot()
    # DAO()
    # await Vocabulary.load_data()
    # Vocabulary()
    # await MessageProcessing.load_data()
    # MinioDAO()
    # await serve()


def run_server():
    """
    Run all in one
    :return:
    """
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     DAO()
    #     executor.submit(run_fastapi)
    #     asyncio.run(run_rpc())


if __name__ == '__main__':
    """
    Main launching modules
    """
    launch_modes = {
        'server': run_server,
        'rpc': run_rpc,
        'rest': run_fastapi
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--custom_run_mode',
                        help='Параметр необходимый для отдельного запуска компонентов',
                        required=False)
    args = parser.parse_args()
    if args.custom_run_mode:
        launch_func = launch_modes.get(args.custom_run_mode)
        if launch_func:
            if launch_func == run_rpc:
                asyncio.run(run_rpc())
            launch_func()
        else:
            print("Неверный режим запуска")
    else:
        run_server()
