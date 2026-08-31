"""Google Drive HTTP client — multipart upload shape and token errors."""
import httpx
import pytest

from app.services.google_drive_client import DriveApiError, GoogleDriveClient


@pytest.mark.asyncio
async def test_create_upload_uses_multipart_related():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"files": []})
        captured["content_type"] = request.headers.get("content-type", "")
        captured["url"] = str(request.url)
        captured["body"] = request.content
        return httpx.Response(200, json={"id": "file-1"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = GoogleDriveClient("token", http)
        file_id = await client.upsert_file("folder-1", "Personal-latest.zip", b"zip-bytes")

    assert file_id == "file-1"
    assert captured["content_type"].startswith("multipart/related;")
    assert "uploadType=multipart" in captured["url"]
    assert b"Personal-latest.zip" in captured["body"]
    assert b"zip-bytes" in captured["body"]


@pytest.mark.asyncio
async def test_user_email_surfaces_google_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_grant"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = GoogleDriveClient("token", http)
        with pytest.raises(DriveApiError, match="invalid_grant"):
            await client.user_email()
