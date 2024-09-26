import jwt
import logging
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

def get_user_from_request(request):
    token = request.COOKIES.get('access_token') or request.COOKIES.get('refresh_token')
    if not token:
        logger.debug("No token found in cookies")
        return None
    try:
        decoded_data = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded_data.get('user_id')
        logger.debug(f"Decoded user_id from token: {user_id}")
        user = User.objects.get(id=user_id)
        logger.debug(f"User found: {user}")
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.error(f"Token error: {e}")
        return None
    except User.DoesNotExist:
        logger.error("User does not exist")
        return None