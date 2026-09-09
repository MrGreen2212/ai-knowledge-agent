from app.main import app


def test_app_imports_and_has_expected_routes():
    assert app is not None
    assert app.title == "AI Knowledge Agent"
    assert "/" in {route.path for route in app.routes}
    assert "/documents/upload" in {route.path for route in app.routes}
    assert "/conversations/chat" in {route.path for route in app.routes}
    assert "/conversations" in {route.path for route in app.routes}
