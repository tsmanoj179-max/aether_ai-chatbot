def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "AetherAI"
    assert data["status"] == "operational"

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "connected"
    assert "mock" in data["configured_providers"]

def test_providers_and_models(client):
    prov_res = client.get("/api/v1/providers")
    assert prov_res.status_code == 200
    provs = prov_res.json()
    assert any(p["name"] == "mock" for p in provs)

    model_res = client.get("/api/v1/models")
    assert model_res.status_code == 200
    models = model_res.json()
    assert any(m["id"] == "aether-mock-omni" for m in models)
