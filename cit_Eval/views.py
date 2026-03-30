from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization, Cipher, algorithms, modes
from .models import Course, Evaluation, DHSession
from .serializers import CourseSerializer, EvaluationSerializer
import uuid
import base64

# Standard DH Parameters (In a real app, use pre-generated 2048-bit group)
parameters = dh.generate_parameters(generator=2, key_size=2048)

class DiffieHellmanHandshakeView(APIView):
    def post(self, request):
        client_public_key_bytes = request.data.get('client_public_key')
        
        if not client_public_key_bytes:
            return Response({"error": "No client key provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Generate Server's Private & Public Key
        server_private_key = parameters.generate_private_key()
        server_public_key = server_private_key.public_key()

        # 2. Serialize Server Public Key to send to React
        server_pub_bytes = server_public_key.public_key_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 3. Load Client's Public Key
        client_public_key = serialization.load_pem_public_key(
            client_public_key_bytes.encode('utf-8')
        )

        # 4. Calculate the Shared Secret
        shared_secret = server_private_key.exchange(client_public_key)
        
        # 5. Store in DHSession (to use for future decryption)
        session_id = str(uuid.uuid4())
        from .models import DHSession
        DHSession.objects.create(
            session_id=session_id,
            client_public_key=client_public_key_bytes,
            server_private_key="HIDDEN_FOR_SECURITY", # Don't store raw private keys!
            shared_secret=shared_secret.hex() # Store the derived secret to decrypt incoming data
        )

        return Response({
            "server_public_key": server_pub_bytes.decode('utf-8'),
            "session_id": session_id
        })
    
class CourseListView(APIView):
    """
    GET: Retrieve all courses for the student to see.
    """
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

class EvaluationSubmitView(APIView):
    """
    POST: Receive encrypted evaluation data, decrypt it, and save it.
    """
    def post(self, request):
        session_id = request.data.get('session_id')
        encrypted_data = request.data.get('payload') # The ciphertext from React
        iv_hex = request.data.get('iv') # Initialization Vector for AES

        try:
            # 1. Retrieve the shared secret from our DB using the session_id
            dh_session = DHSession.objects.get(session_id=session_id)
            shared_secret = bytes.fromhex(dh_session.shared_secret)[:32] # Use first 32 bytes for AES-256
            
            # 2. Decrypt the data (AES-GCM or AES-CBC)
            # This is a simplified AES decryption example
            iv = bytes.fromhex(iv_hex)
            cipher = Cipher(algorithms.AES(shared_secret), modes.CBC(iv))
            decryptor = cipher.decryptor()
            
            # Decrypt and decode JSON (handling padding if necessary)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
            
            # 3. Clean and parse the JSON (Note: In production, use proper padding removal)
            import json
            data = json.loads(decrypted_padded_data.decode('utf-8').strip())

            # 4. Pass decrypted data to Serializer to save to PostgreSQL
            serializer = EvaluationSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "Success", "message": "Evaluation secured and saved."}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except DHSession.DoesNotExist:
            return Response({"error": "Invalid Session"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"Decryption failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)