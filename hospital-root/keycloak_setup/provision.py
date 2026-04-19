import os
import time
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

# Global Configuration
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080/")
KEYCLOAK_ADMIN = os.environ.get("KEYCLOAK_ADMIN", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin")

REALM_NAME = "hms-realm"
CLIENT_ID = "hms-app"
SUPER_USER = "super_admin"
SUPER_USER_PWD = "Admin@123"

ROLES = [
    "PATIENT_VIEW",
    "PATIENT_CREATE",
    "CLINICAL_WRITE",
    "LAB_RESULT_APPROVE",
    "BILLING_ADMIN",
    "PHARMACY_DISPENSE"
]

def wait_for_keycloak(keycloak_admin, max_retries=10, delay_sec=5):
    """Wait until Keycloak is ready to accept requests."""
    for i in range(max_retries):
        try:
            # A simple call to verify availability
            keycloak_admin.get_realms()
            return True
        except Exception as e:
            print(f"Waiting for Keycloak to be ready... ({i+1}/{max_retries})")
            time.sleep(delay_sec)
    return False

def main():
    print(f"Connecting to Keycloak Admin at {KEYCLOAK_URL}...")
    
    try:
        # Initialize the admin connection to the master realm
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=KEYCLOAK_ADMIN,
            password=KEYCLOAK_ADMIN_PASSWORD,
            realm_name="master",
            verify=True
        )
    except Exception as e:
        print(f"Failed to connect to Keycloak: {e}")
        return

    if not wait_for_keycloak(keycloak_admin):
        print("Keycloak is not ready. Exiting.")
        return

    # 1. Create Realm
    print(f"Configuring Realm: {REALM_NAME}")
    try:
        keycloak_admin.create_realm(payload={"realm": REALM_NAME, "enabled": True})
        print(f" - Created realm {REALM_NAME}")
    except KeycloakError as e:
        if e.response_code == 409:
            print(f" - Realm {REALM_NAME} already exists (idempotent)")
        else:
            raise e

    # Switch scope to new realm
    keycloak_admin.realm_name = REALM_NAME

    # 2. Create Client
    print(f"Configuring Client: {CLIENT_ID}")
    try:
        client_payload = {
            "clientId": CLIENT_ID,
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "redirectUris": ["*"],
            "webOrigins": ["+"]
        }
        keycloak_admin.create_client(payload=client_payload)
        print(f" - Created client {CLIENT_ID}")
    except KeycloakError as e:
        if e.response_code == 409:
            print(f" - Client {CLIENT_ID} already exists (idempotent)")
        else:
            raise e

    # Retrieve Client ID (internal UUID) for later mapping if needed, though we map realm roles.
    # 3. Create Realm Roles
    print("Configuring Roles...")
    for role in ROLES:
        try:
            keycloak_admin.create_realm_role(payload={"name": role})
            print(f" - Created role: {role}")
        except KeycloakError as e:
            if e.response_code == 409:
                print(f" - Role {role} already exists (idempotent)")
            else:
                raise e

    # 4. Create Super User
    print(f"Configuring User: {SUPER_USER}")
    try:
        user_payload = {
            "username": SUPER_USER,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"value": SUPER_USER_PWD, "type": "password", "temporary": False}]
        }
        new_user_uuid = keycloak_admin.create_user(payload=user_payload)
        print(f" - Created user: {SUPER_USER}")
        user_id = new_user_uuid
    except KeycloakError as e:
        if e.response_code == 409:
            print(f" - User {SUPER_USER} already exists (idempotent)")
            user_id = keycloak_admin.get_user_id(SUPER_USER)
        else:
            raise e
            
    # 5. Map Roles to Super User
    print(f"Assigning roles to {SUPER_USER}...")
    roles_dicts = []
    for role in ROLES:
        role_obj = keycloak_admin.get_realm_role(role)
        if role_obj:
            roles_dicts.append(role_obj)
            
    if roles_dicts:
        keycloak_admin.assign_realm_roles(user_id=user_id, roles=roles_dicts)
        print(" - Successfully assigned realm roles to user.")
        
    print("\n" + "="*40)
    print(" SUCCESS SUMMARY ")
    print("="*40)
    print(f"Realm: {REALM_NAME}")
    print(f"Client: {CLIENT_ID} (Public)")
    print(f"Super User: {SUPER_USER}")
    print("Assigned Roles:")
    for r in ROLES:
        print(f" - {r}")
    print("="*40)

if __name__ == "__main__":
    main()
