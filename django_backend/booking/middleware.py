from django.http import JsonResponse


class ApiCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and request.method == "OPTIONS":
            response = JsonResponse({}, status=204)
        else:
            response = self.get_response(request)

        if request.path.startswith("/api/"):
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
