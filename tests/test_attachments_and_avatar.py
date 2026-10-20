import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import create_verified_user, get_token

# Helper to create valid fake files with magic bytes
def create_fake_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"

def create_fake_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def test_avatar_upload_and_removal(client: TestClient, db_session: Session):
    user = create_verified_user(db_session, "avatar_user@example.com", "Avatar User")
    token = get_token(client, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Reject invalid avatar format (e.g. text or script disguised as image)
    res_invalid = client.put(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("fake.png", io.BytesIO(b"alert('malicious script');"), "image/png")},
    )
    assert res_invalid.status_code == 400
    assert "Invalid avatar format" in res_invalid.json()["detail"]

    # 2. Upload valid PNG avatar
    png_bytes = create_fake_png()
    res_valid = client.put(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("profile.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["avatar_url"] == f"/api/v1/users/{user.id}/avatar"

    # 3. Retrieve avatar image
    res_get = client.get(f"/api/v1/users/{user.id}/avatar")
    assert res_get.status_code == 200
    assert res_get.headers["content-type"] == "image/png"
    assert res_get.content == png_bytes

    # 4. Remove avatar
    res_del = client.delete("/api/v1/users/me/avatar", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["avatar_url"] is None

    # 5. Check retrieval after deletion returns 404
    res_get_after = client.get(f"/api/v1/users/{user.id}/avatar")
    assert res_get_after.status_code == 404


def test_comment_attachment_workflow(client: TestClient, db_session: Session):
    owner = create_verified_user(db_session, "owner_attach@example.com", "Attach Owner")
    token = get_token(client, owner.email)
    headers = {"Authorization": f"Bearer {token}"}

    # Create workspace, project, task, comment
    ws_res = client.post("/api/v1/workspaces/", headers=headers, json={"name": "Attach Space", "slug": "attach-space"})
    assert ws_res.status_code == 201

    proj_res = client.post(
        "/api/v1/workspaces/attach-space/projects/",
        headers=headers,
        json={"name": "Attach Project", "key": "ATT"},
    )
    assert proj_res.status_code == 201

    task_res = client.post(
        "/api/v1/workspaces/attach-space/projects/ATT/tasks/",
        headers=headers,
        json={"title": "Task with attachments"},
    )
    assert task_res.status_code == 201
    task_num = task_res.json()["task_number"]

    comment_res = client.post(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/",
        headers=headers,
        json={"content": "Initial comment text"},
    )
    assert comment_res.status_code == 201
    comment_id = comment_res.json()["id"]

    # 1. Reject invalid file format (e.g. SVG or executable)
    res_bad = client.post(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/{comment_id}/attachments",
        headers=headers,
        files=[("files", ("evil.svg", io.BytesIO(b"<svg><script>alert(1)</script></svg>"), "image/svg+xml"))],
    )
    assert res_bad.status_code == 400

    # 2. Upload valid PNG and PDF
    png_content = create_fake_png()
    pdf_content = create_fake_pdf()
    res_upload = client.post(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/{comment_id}/attachments",
        headers=headers,
        files=[
            ("files", ("diagram.png", io.BytesIO(png_content), "image/png")),
            ("files", ("specs.pdf", io.BytesIO(pdf_content), "application/pdf")),
        ],
    )
    assert res_upload.status_code == 201
    attachments = res_upload.json()
    assert len(attachments) == 2
    png_id = attachments[0]["id"]
    pdf_id = attachments[1]["id"]

    # 3. Check comment includes attachments in list
    comments_res = client.get(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/",
        headers=headers,
    )
    assert comments_res.status_code == 200
    listed_comments = comments_res.json()
    assert len(listed_comments) == 1
    assert len(listed_comments[0]["attachments"]) == 2

    # 4. Download attachment
    download_res = client.get(f"/api/v1/attachments/{png_id}/download", headers=headers)
    assert download_res.status_code == 200
    assert "attachment" in download_res.headers["content-disposition"]
    assert download_res.content == png_content

    # 5. Preview attachment
    preview_res = client.get(f"/api/v1/attachments/{pdf_id}/preview", headers=headers)
    assert preview_res.status_code == 200
    assert "inline" in preview_res.headers["content-disposition"]
    assert preview_res.content == pdf_content

    # 6. Delete attachment
    del_res = client.delete(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/{comment_id}/attachments/{png_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    # 7. Check deleted attachment is excluded from comment and download
    comm_after_del = client.get(
        f"/api/v1/workspaces/attach-space/projects/ATT/tasks/{task_num}/comments/",
        headers=headers,
    )
    assert len(comm_after_del.json()[0]["attachments"]) == 1

    download_del = client.get(f"/api/v1/attachments/{png_id}/download", headers=headers)
    assert download_del.status_code == 404
