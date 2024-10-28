import grpc
from grpc.aio import ServerInterceptor


class SignatureValidationInterceptor(ServerInterceptor):
    def __init__(self):
        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid signature")

        self._abort_handler = grpc.unary_unary_rpc_method_handler(abort)

    async def intercept_service(self, continuation, handler_call_details):
        """
        Validate signature for user token if not valid - abort rpc and return error data
        :param continuation:
        :param handler_call_details:
        :return:
        """