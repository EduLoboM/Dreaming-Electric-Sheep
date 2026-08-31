import pytest

from dreaming_electric_sheep.routing import CythonRadixRouter, RadixTree
from dreaming_electric_sheep.server.routing import Route, RouteMethod, Router


def test_radix_tree_static_routes():
    tree = RadixTree()

    def home(): ...
    def api_users(): ...
    def api_health(): ...

    r_home = Route(b"/", home)
    r_users = Route(b"/api/users", api_users)
    r_health = Route(b"/api/health", api_health)

    tree.insert(b"/", r_home)
    tree.insert(b"/api/users", r_users)
    tree.insert(b"/api/health", r_health)

    # Exact matches
    match, params = tree.match(b"/")
    assert match is r_home
    assert params is None

    match, params = tree.match(b"/api/users")
    assert match is r_users
    assert params is None

    # Trailing slash support
    match, params = tree.match(b"/api/users/")
    assert match is r_users
    assert params is None

    # Non existing route
    assert tree.match(b"/api/notfound") is None
    assert tree.match(b"/api/users//") is None


def test_radix_tree_parameterized_routes():
    tree = RadixTree()

    def get_user(): ...
    def get_user_post(): ...

    r_user = Route(b"/users/{id}", get_user)
    r_post = Route(b"/users/{user_id}/posts/{post_id}", get_user_post)

    tree.insert(b"/users/{id}", r_user)
    tree.insert(b"/users/{user_id}/posts/{post_id}", r_post)

    # Match single param
    match, params = tree.match(b"/users/42")
    assert match is r_user
    assert params == {"id": "42"}

    # Match multi param with URL decoding
    match, params = tree.match(b"/users/john%20doe/posts/101")
    assert match is r_post
    assert params == {"user_id": "john doe", "post_id": "101"}


def test_radix_tree_typed_parameter_validators():
    tree = RadixTree()

    def get_by_int(): ...
    def get_by_uuid(): ...

    r_int = Route(b"/items/{int:item_id}", get_by_int)
    r_uuid = Route(b"/files/{uuid:file_id}", get_by_uuid)

    tree.insert(b"/items/{int:item_id}", r_int)
    tree.insert(b"/files/{uuid:file_id}", r_uuid)

    # Valid int
    match, params = tree.match(b"/items/12345")
    assert match is r_int
    assert params == {"item_id": "12345"}

    # Invalid int should not match
    assert tree.match(b"/items/abc") is None

    # Valid UUID
    valid_uuid = b"a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    match, params = tree.match(b"/files/" + valid_uuid)
    assert match is r_uuid
    assert params == {"file_id": valid_uuid.decode()}

    # Invalid UUID
    assert tree.match(b"/files/invalid-uuid-format") is None


def test_radix_tree_wildcard_catchall():
    tree = RadixTree()

    def static_files(): ...
    def js_files(): ...

    r_static = Route(b"/static/*", static_files)
    r_js = Route(b"/assets/*.js", js_files)

    tree.insert(b"/static/*", r_static)
    tree.insert(b"/assets/*.js", r_js)

    match, params = tree.match(b"/static/css/main.css")
    assert match is r_static
    assert params == {"tail": "css/main.css"}

    match, params = tree.match(b"/assets/bundle.min.js")
    assert match is r_js
    assert params == {"tail": "bundle.min"}

    assert tree.match(b"/assets/bundle.min.css") is None


def test_cython_radix_router_method_dispatch():
    router = CythonRadixRouter()

    def get_users(): ...
    def post_users(): ...
    def delete_users(): ...

    r_get = Route(b"/users", get_users)
    r_post = Route(b"/users", post_users)
    r_del = Route(b"/users/{id}", delete_users)

    router.add_route(b"GET", b"/users", r_get)
    router.add_route(b"POST", b"/users", r_post)
    router.add_route(b"DELETE", b"/users/{id}", r_del)

    match_get = router.get_match(b"GET", b"/users")
    assert match_get[0] is r_get

    match_post = router.get_match(b"POST", b"/users")
    assert match_post[0] is r_post

    match_del = router.get_match(b"DELETE", b"/users/99")
    assert match_del[0] is r_del
    assert match_del[1] == {"id": "99"}

    assert router.get_match(b"PUT", b"/users") is None
