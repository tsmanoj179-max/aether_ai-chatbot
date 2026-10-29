def test_memories_crud(client):
    # 1. Create memory
    res = client.post(
        "/api/v1/memories",
        json={"content": "Prefer concise TypeScript examples.", "category": "preference"}
    )
    assert res.status_code == 200
    mem_data = res.json()
    mem_id = mem_data["id"]
    assert mem_data["content"] == "Prefer concise TypeScript examples."
    assert mem_data["is_active"] is True

    # 2. List memories
    list_res = client.get("/api/v1/memories")
    assert list_res.status_code == 200
    all_mems = list_res.json()
    assert any(m["id"] == mem_id for m in all_mems)

    # 3. Update memory
    patch_res = client.patch(
        f"/api/v1/memories/{mem_id}",
        json={"content": "Prefer Python and TypeScript."}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["content"] == "Prefer Python and TypeScript."

    # 4. Delete memory
    del_res = client.delete(f"/api/v1/memories/{mem_id}")
    assert del_res.status_code == 200

    # 5. Verify deleted
    list_after = client.get("/api/v1/memories").json()
    assert not any(m["id"] == mem_id for m in list_after)
