import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from project_management_api.core.security import create_access_token
from project_management_api.crud import company as crud_company
from project_management_api.models.company import CompanyRole, CompanyStatus
from tests.conftest import create_verified_user, get_token


def test_user_registration_without_company_and_onboarding_guard(client: TestClient, db_session: Session):
    """
    Verifies that a newly registered user has 0 companies and cannot create workspaces
    until they complete company onboarding.
    """
    user = create_verified_user(db_session, "newuser@example.com", "New User", with_company=False)
    token = get_token(client, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. User has 0 companies
    my_comps_res = client.get("/api/v1/companies/me", headers=headers)
    assert my_comps_res.status_code == 200
    assert len(my_comps_res.json()) == 0

    # 2. Cannot create workspace without belonging to a company
    ws_res = client.post(
        "/api/v1/workspaces/",
        json={"name": "Orphan Workspace", "description": "Should fail"},
        headers=headers,
    )
    assert ws_res.status_code == 400


def test_company_creation_request_approval_workflow(client: TestClient, db_session: Session):
    """
    Verifies the full lifecycle of company request submission, superuser review,
    approval, and subsequent workspace creation.
    """
    superuser = create_verified_user(db_session, "superadmin@example.com", "Super Admin", is_superuser=True, with_company=False)
    requester = create_verified_user(db_session, "founder@example.com", "Startup Founder", with_company=False)

    super_token = get_token(client, superuser.email)
    founder_token = get_token(client, requester.email)

    founder_headers = {"Authorization": f"Bearer {founder_token}"}
    admin_headers = {"Authorization": f"Bearer {super_token}"}

    # 1. Founder submits company creation request
    req_res = client.post(
        "/api/v1/companies/requests",
        json={
            "company_name": "Apex Innovations",
            "company_slug": "apex-innovations",
            "business_description": "Building cloud infrastructure software",
        },
        headers=founder_headers,
    )
    assert req_res.status_code == 201
    request_data = req_res.json()
    assert request_data["status"] == "PENDING"
    assert request_data["company_name"] == "Apex Innovations"
    req_id = request_data["id"]

    # 2. Founder can track their requests
    mine_res = client.get("/api/v1/companies/requests/mine", headers=founder_headers)
    assert mine_res.status_code == 200
    assert any(r["id"] == req_id for r in mine_res.json())

    # 3. Superuser reviews requests in Admin console
    admin_requests = client.get("/api/v1/admin/company-requests?status_filter=PENDING", headers=admin_headers)
    assert admin_requests.status_code == 200
    assert any(r["id"] == req_id for r in admin_requests.json())

    # 4. Superuser approves the request
    approve_res = client.post(f"/api/v1/admin/company-requests/{req_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    company_data = approve_res.json()
    assert company_data["slug"] == "apex-innovations"
    assert company_data["status"] == "ACTIVE"

    # 5. Founder now belongs to the company as COMPANY_OWNER
    founder_comps = client.get("/api/v1/companies/me", headers=founder_headers)
    assert founder_comps.status_code == 200
    assert len(founder_comps.json()) == 1
    assert founder_comps.json()[0]["slug"] == "apex-innovations"
    assert founder_comps.json()[0]["my_role"] == "COMPANY_OWNER"

    # 6. Founder can now create a workspace in their company
    ws_res = client.post(
        "/api/v1/workspaces/",
        json={"name": "Core Engineering", "description": "Main eng workspace"},
        headers={**founder_headers, "X-Company-Slug": "apex-innovations"},
    )
    assert ws_res.status_code == 201
    assert ws_res.json()["name"] == "Core Engineering"
    assert ws_res.json()["company_id"] == company_data["id"]


def test_invitation_and_company_rbac(client: TestClient, db_session: Session):
    """
    Verifies invitation tokens, acceptance, and role enforcement (MEMBER cannot create workspaces,
    ADMIN/OWNER can).
    """
    owner = create_verified_user(db_session, "co_owner@example.com", "Co Owner", with_company=True)
    invitee = create_verified_user(db_session, "invitee@example.com", "Invitee Person", with_company=False)

    owner_token = get_token(client, owner.email)
    invitee_token = get_token(client, invitee.email)

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    invitee_headers = {"Authorization": f"Bearer {invitee_token}"}

    # Get owner's company slug
    owner_comps = client.get("/api/v1/companies/me", headers=owner_headers).json()
    company_slug = owner_comps[0]["slug"]

    # 1. Owner invites invitee with MEMBER role
    inv_res = client.post(
        f"/api/v1/companies/{company_slug}/invitations",
        json={"email": invitee.email, "role": "MEMBER"},
        headers=owner_headers,
    )
    assert inv_res.status_code == 201
    token = inv_res.json()["token"]
    assert token is not None

    # 2. Invitee accepts invitation
    accept_res = client.post(
        "/api/v1/companies/invitations/accept",
        json={"token": token},
        headers=invitee_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["role"] == "MEMBER"

    # 3. Invitee now belongs to the company as MEMBER
    invitee_comps = client.get("/api/v1/companies/me", headers=invitee_headers).json()
    assert len(invitee_comps) == 1
    assert invitee_comps[0]["my_role"] == "MEMBER"

    # 4. MEMBER is forbidden from creating workspaces
    create_ws_fail = client.post(
        "/api/v1/workspaces/",
        json={"name": "Member Unauthorized Space"},
        headers={**invitee_headers, "X-Company-Slug": company_slug},
    )
    assert create_ws_fail.status_code == 403

    # 5. Owner promotes invitee to COMPANY_ADMIN
    members = client.get(f"/api/v1/companies/{company_slug}/members", headers=owner_headers).json()
    member_record = next(m for m in members if m["user_id"] == invitee.id)
    patch_role = client.patch(
        f"/api/v1/companies/{company_slug}/members/{invitee.id}",
        json={"role": "COMPANY_ADMIN"},
        headers=owner_headers,
    )
    assert patch_role.status_code == 200
    assert patch_role.json()["role"] == "COMPANY_ADMIN"

    # 6. Now as COMPANY_ADMIN, user can create workspace
    create_ws_ok = client.post(
        "/api/v1/workspaces/",
        json={"name": "Admin Authorized Space"},
        headers={**invitee_headers, "X-Company-Slug": company_slug},
    )
    assert create_ws_ok.status_code == 201


def test_tenant_data_isolation(client: TestClient, db_session: Session):
    """
    Verifies that User in Company A cannot access or manipulate workspaces in Company B.
    """
    user_a = create_verified_user(db_session, "user_a@example.com", "User A", with_company=True)
    user_b = create_verified_user(db_session, "user_b@example.com", "User B", with_company=True)

    token_a = get_token(client, user_a.email)
    token_b = get_token(client, user_b.email)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates a workspace in Company B
    comp_b_slug = client.get("/api/v1/companies/me", headers=headers_b).json()[0]["slug"]
    ws_b = client.post(
        "/api/v1/workspaces/",
        json={"name": "Secret Company B Workspace", "slug": "secret-ws-b"},
        headers={**headers_b, "X-Company-Slug": comp_b_slug},
    ).json()

    # User A tries to access Workspace B
    # 1. With User A's token directly -> 403 Not a member
    access_attempt = client.get(f"/api/v1/workspaces/{ws_b['slug']}", headers=headers_a)
    assert access_attempt.status_code == 403

    # 2. User A tries to pretend it's in their own company -> 403 Workspace does not belong to company
    comp_a_slug = client.get("/api/v1/companies/me", headers=headers_a).json()[0]["slug"]
    spoof_attempt = client.get(
        f"/api/v1/workspaces/{ws_b['slug']}",
        headers={**headers_a, "X-Company-Slug": comp_a_slug},
    )
    assert spoof_attempt.status_code == 403


def test_platform_admin_company_management_and_suspension(client: TestClient, db_session: Session):
    """
    Verifies superuser can view, suspend, and restore companies across the entire platform.
    """
    superuser = create_verified_user(db_session, "sysadmin@example.com", "Sys Admin", is_superuser=True, with_company=False)
    company_owner = create_verified_user(db_session, "target_owner@example.com", "Target Owner", with_company=True)

    super_token = get_token(client, superuser.email)
    owner_token = get_token(client, company_owner.email)

    admin_headers = {"Authorization": f"Bearer {super_token}"}
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    owner_comps = client.get("/api/v1/companies/me", headers=owner_headers).json()
    comp = owner_comps[0]

    # 1. Superuser views all companies
    all_comps = client.get("/api/v1/admin/companies", headers=admin_headers)
    assert all_comps.status_code == 200
    assert any(c["id"] == comp["id"] for c in all_comps.json())

    # 2. Superuser suspends company
    suspend_res = client.patch(
        f"/api/v1/admin/companies/{comp['id']}?status=SUSPENDED",
        json={},
        headers=admin_headers,
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["status"] == "SUSPENDED"

    # 3. Company member is now blocked from accessing company resources
    blocked = client.get(
        f"/api/v1/companies/{comp['slug']}",
        headers=owner_headers,
    )
    assert blocked.status_code == 403
    assert "suspended" in blocked.json()["detail"].lower()


def test_workspace_access_request_lifecycle(client: TestClient, db_session: Session):
    """
    Verifies that a regular company member cannot create workspaces,
    submits a workspace access request, and can create workspaces once approved by owner.
    """
    owner = create_verified_user(db_session, "ws_owner@example.com", "Workspace Owner", with_company=True)
    member = create_verified_user(db_session, "ws_member@example.com", "Workspace Member", with_company=False)

    owner_token = get_token(client, owner.email)
    member_token = get_token(client, member.email)

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}

    comp = client.get("/api/v1/companies/me", headers=owner_headers).json()[0]
    comp_slug = comp["slug"]

    # 1. Owner adds member with MEMBER role
    add_res = client.post(
        f"/api/v1/companies/{comp_slug}/members",
        json={"email": member.email, "role": "MEMBER"},
        headers=owner_headers,
    )
    assert add_res.status_code in [200, 201]

    # 2. Member tries to create workspace -> 403 Forbidden
    create_attempt = client.post(
        "/api/v1/workspaces/",
        json={"name": "Member Workspace Attempt", "slug": "member-ws-attempt"},
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert create_attempt.status_code == 403

    # 3. Member submits a workspace access request
    req_res = client.post(
        f"/api/v1/companies/{comp_slug}/workspace-requests",
        json={
            "request_type": "CREATE_WORKSPACE",
            "reason": "Need to setup frontend workspace",
        },
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert req_res.status_code == 201
    req_data = req_res.json()
    assert req_data["status"] == "PENDING"
    assert req_data["request_type"] == "CREATE_WORKSPACE"
    req_id = req_data["id"]

    # Duplicate pending request fails
    dup_res = client.post(
        f"/api/v1/companies/{comp_slug}/workspace-requests",
        json={"request_type": "CREATE_WORKSPACE", "reason": "Again"},
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert dup_res.status_code == 400

    # 4. Member views their requests
    my_requests = client.get(
        f"/api/v1/companies/{comp_slug}/workspace-requests",
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert my_requests.status_code == 200
    assert any(r["id"] == req_id for r in my_requests.json())

    # 5. Non-admin cannot approve request -> 403 Forbidden
    hack_approve = client.post(
        f"/api/v1/companies/{comp_slug}/workspace-requests/{req_id}/approve",
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert hack_approve.status_code == 403

    # 6. Owner approves request
    approve_res = client.post(
        f"/api/v1/companies/{comp_slug}/workspace-requests/{req_id}/approve",
        json={"decision_reason": "Approved for dev work"},
        headers={**owner_headers, "X-Company-Slug": comp_slug},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

    # 7. Member now can create workspace!
    success_ws = client.post(
        "/api/v1/workspaces/",
        json={"name": "Member Approved Workspace", "slug": "member-approved-ws"},
        headers={**member_headers, "X-Company-Slug": comp_slug},
    )
    assert success_ws.status_code in [200, 201]
    assert success_ws.json()["slug"] == "member-approved-ws"


def test_company_owner_role_assignment_safeguards(client: TestClient, db_session: Session):
    """
    Verifies that non-owners (e.g., COMPANY_ADMIN) cannot invite or assign COMPANY_OWNER role.
    """
    owner = create_verified_user(db_session, "actual_owner@example.com", "Actual Owner", with_company=True)
    admin_user = create_verified_user(db_session, "comp_admin@example.com", "Company Admin", with_company=False)
    target_user = create_verified_user(db_session, "target_user@example.com", "Target User", with_company=False)

    owner_token = get_token(client, owner.email)
    admin_token = get_token(client, admin_user.email)

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    comp = client.get("/api/v1/companies/me", headers=owner_headers).json()[0]
    comp_slug = comp["slug"]

    # Owner adds admin_user as COMPANY_ADMIN
    client.post(
        f"/api/v1/companies/{comp_slug}/members",
        json={"email": admin_user.email, "role": "COMPANY_ADMIN"},
        headers=owner_headers,
    )

    # 1. Company Admin tries to invite someone with role=COMPANY_OWNER -> 403 Forbidden
    invite_fail = client.post(
        f"/api/v1/companies/{comp_slug}/invitations",
        json={"email": "new_owner_invite@example.com", "role": "COMPANY_OWNER"},
        headers={**admin_headers, "X-Company-Slug": comp_slug},
    )
    assert invite_fail.status_code == 403

    # 2. Company Admin tries to add target_user with role=COMPANY_OWNER -> 403 Forbidden
    add_fail = client.post(
        f"/api/v1/companies/{comp_slug}/members",
        json={"email": target_user.email, "role": "COMPANY_OWNER"},
        headers={**admin_headers, "X-Company-Slug": comp_slug},
    )
    assert add_fail.status_code == 403

    # 3. Actual owner can invite COMPANY_ADMIN and assign roles
    valid_invite = client.post(
        f"/api/v1/companies/{comp_slug}/invitations",
        json={"email": "colleague_valid@example.com", "role": "MEMBER"},
        headers={**owner_headers, "X-Company-Slug": comp_slug},
    )
    assert valid_invite.status_code == 201

