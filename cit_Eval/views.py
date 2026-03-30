from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # FIXED

from .models import Course, DHSession
from .serializers import CourseSerializer, EvaluationSerializer

import uuid
import base64
import json

parameters = dh.generate_parameters(generator=2, key_size=2048)

class DiffieHellmanHandshakeView(APIView):
    def post(self, request):
        client_public_key_bytes = request.data.get("client_public_key")
        if not client_public_key_bytes:
            return Response({"error": "No client key provided"}, status=status.HTTP_400_BAD_REQUEST)

        server_private_key = parameters.generate_private_key()
        server_public_key = server_private_key.public_key()

        server_pub_bytes = server_public_key.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        client_public_key = serialization.load_pem_public_key(
            client_public_key_bytes.encode("utf-8")
        )

        shared_secret = server_private_key.exchange(client_public_key)

        session_id = str(uuid.uuid4())
        DHSession.objects.create(
            session_id=session_id,
            client_public_key=client_public_key_bytes,
            server_private_key="HIDDEN_FOR_SECURITY",
            shared_secret=shared_secret.hex(),
        )

        return Response(
            {"server_public_key": server_pub_bytes.decode("utf-8"), "session_id": session_id}
        )

class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

class EvaluationSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Recommended: accept plain JSON over HTTPS instead of custom crypto
        serializer = EvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "Success"}, status=status.HTTP_201_CREATED)