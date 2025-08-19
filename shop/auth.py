# shop/auth.py
from typing import Optional, Tuple
from types import SimpleNamespace
from rest_framework.authentication import BaseAuthentication

class RoleHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request) -> Optional[Tuple[object, None]]:
        role = request.headers.get("X-Role", "user").lower()
        user_id = request.headers.get("X-User-Id", "guest")
        user = SimpleNamespace(
            is_authenticated=True,
            role=role,
            user_id=user_id,
            is_staff=(role == "admin"),
            is_superuser=False,
        )
        return (user, None)
