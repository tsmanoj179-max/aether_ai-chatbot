def test_conversation_crud_and_persistence(client):
    # 1. Create conversation
    create_res = client.post(
        "/api/v1/conversations",
        json={"title": "Test Chat", "model_id": "aether-mock-omni"}
    )
    assert create_res.status_code == 200
    conv_data = create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Test Chat"

    # 2. List conversations
    list_res = client.get("/api/v1/conversations")
    assert list_res.status_code == 200
    conv_list = list_res.json()
    assert any(c["id"] == conv_id for c in conv_list)

    # 3. Update conversation (pin and rename)
    patch_res = client.patch(
        f"/api/v1/conversations/{conv_id}",
        json={"title": "Updated Title", "pinned": True}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"
    assert patch_res.json()["pinned"] is True

    # 4. Stream chat response into conversation
    stream_res = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": conv_id,
            "message": "Write a python function to compute factorial"
        }
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]
    body = stream_res.text
    assert "data: " in body
    assert "token" in body

    # 5. Fetch details and verify messages persisted
    details_res = client.get(f"/api/v1/conversations/{conv_id}")
    assert details_res.status_code == 200
    details = details_res.json()
    assert len(details["messages"]) >= 2
    user_msg = details["messages"][0]
    asst_msg = details["messages"][1]
    assert user_msg["role"] == "user"
    assert asst_msg["role"] == "assistant"

    # 6. Delete conversation
    del_res = client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/v1/conversations/{conv_id}").status_code == 404
