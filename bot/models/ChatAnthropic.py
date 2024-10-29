
class CustomChatAnthropic(ChatAnthropic):
    def __init__(self, arg_model: str = 'claude-3-5-sonnet-20240620'):
        super(CustomChatAnthropic, self).__init__(model=arg_model)
        self._async_client._client = DefaultAsyncHttpxClient(proxies=os.getenv("SOME_PROXY_HTTP"),
                                                             transport=httpx.AsyncHTTPTransport(local_address="0.0.0.0")
                                                             )