from typing import Set

VALID_ROLES: Set[str] = {"all_employees", "manager", "admin"}

# Access hierarchy: higher levels inherit access to lower levels
ROLE_PERMISSIONS = {
    "all_employees": {"all_employees"},
    "manager": {"all_employees", "manager"},
    "admin": {"all_employees", "manager", "admin"},
}


def is_authorized(user_role: str, document_access_level: str) -> bool:
    """
    Validates whether the user's role grants permission to view the document.
    Defaults to strict denial if unknown role or level is passed.
    """
    clean_role = user_role.lower().strip()
    clean_level = document_access_level.lower().strip()

    allowed_levels = ROLE_PERMISSIONS.get(clean_role, {"all_employees"})
    return clean_level in allowed_levels

