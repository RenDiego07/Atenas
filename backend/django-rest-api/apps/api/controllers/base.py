from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class BaseController(APIView):
    def handle_response(self, data, status_code=status.HTTP_200_OK):
        return Response(data, status=status_code)

    def handle_error(self, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({'error': error_message}, status=status_code)