from app import create_app


def test_home_page_loads():
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
