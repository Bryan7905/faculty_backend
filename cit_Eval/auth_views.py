import os

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


def issue_jwt_for_user(user: User):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class GoogleLoginView(APIView):
    """
    Exchange a Google ID token for *your* JWT tokens.
    React sends: { "id_token": "<google_id_token>" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        google_id_token = request.data.get("id_token")
        if not google_id_token:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        google_client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        if not google_client_id:
            return Response(
                {"error": "Server missing GOOGLE_OAUTH_CLIENT_ID env var"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            idinfo = id_token.verify_oauth2_token(
                google_id_token,
                google_requests.Request(),
                google_client_id,
            )
        except Exception:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Basic claims
        email = idinfo.get("email")
        email_verified = idinfo.get("email_verified", False)

        if not email or not email_verified:
            return Response(
                {"error": "Google email not verified"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Optional: restrict to your school domain (Google Workspace)
        allowed_domain = os.environ.get("GSUITE_DOMAIN")  # e.g. "mycollege.edu"
        if allowed_domain:
            # 1) Require Google Workspace hosted domain claim (prevents most personal accounts)
            hd = idinfo.get("hd")
            if hd != allowed_domain:
                return Response(
                    {"error": "Only organization Google Workspace accounts are allowed."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        
            # 2) Also enforce email domain as a backup
            email = (email or "").lower()
            if not email.endswith("@" + allowed_domain.lower()):
                return Response(
                    {"error": "Only organization email addresses are allowed."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Create or get user
        user, created = User.objects.get_or_create(
            username=email,   # simple choice
            defaults={"email": email, "role": "student"},
        )
        if not user.email:
            user.email = email
            user.save(update_fields=["email"])

        tokens = issue_jwt_for_user(user)
        return Response(
            {"tokens": tokens, "user": {"id": user.id, "username": user.username, "email": user.email}},
            status=status.HTTP_200_OK,
        )