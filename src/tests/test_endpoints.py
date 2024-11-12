import pytest
import jwt
from datetime import datetime

from fastapi.testclient import TestClient

from ..main import app
from .conftest import test_user_data, test_settings


client = TestClient(app)


def test_register_new_user(plain_sql_connection):
    email = 'good@email.com'
    response = client.post(
        url='/auth/register',
        json={
            'email': email,
            'password': 'GoodPassword12#'
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        'detail': 'Successful registration! You can use now your credentials to get a token.'
    }
    check_entry = plain_sql_connection.execute(
        "SELECT email, autoreply_timeout FROM users WHERE email=?;",
        (email, )
    )
    assert check_entry.fetchone() == (email, None), 'Database entry isn\'t the one that expected'


def test_register_existing_user():
    response = client.post(
        url='/auth/register',
        json={
            'email': test_user_data['username'],
            'password': test_user_data['password']
        }
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': 'This email has already been used',
    }


@pytest.mark.parametrize(
    ('email', 'password'),
    (
        ('invalid-email.com', 'GoodPassword12#'),
        ('invalid@email', 'GoodPassword12#'),
        ('invalid@email,com', 'GoodPassword12#'),
        ('@email.com', 'GoodPassword12#'),
        ('invalid@.com', 'GoodPassword12#'),
        ('onemoregood@email.com', 'BadPassword'),
        ('onemoregood@email.com', 't0OF3w!'),
        ('onemoregood@email.com', '12345678Aa'),
        ('onemoregood@email.com', 'AaAaAaAa!#'),
        ('onemoregood@email.com', '1234#!@#'),
    )
)
def test_register_bad_creds(email, password):
    response = client.post(
        url='/auth/register',
        json={
            'email': email,
            'password': password
        }
    )
    assert response.status_code == 422


def test_issue_token_success():
    response = client.post(
        "/auth/token",
        data=test_user_data,
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"].lower() == "bearer"

    decoded_token = jwt.decode(token_data["access_token"], test_settings.secret_key, algorithms=["HS256"])
    assert decoded_token["sub"] == 1
    assert decoded_token["exp"] > datetime.now().timestamp()


@pytest.mark.parametrize(
    ('username', 'password'),
    (
        (test_user_data['username'], 'GoodPassword12#'),
        (test_user_data['username'], test_user_data['password'] + 'l'),
        ('nonexisting@email.com', test_user_data['password']),
    )
)
def test_get_auth_token_bad_password(username, password):
    response = client.post(
        "/auth/token",
        data={
            "username": username,
            "password": password
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect username or password"}


# Test retrieving the current user's data
def test_get_user_me():
    # Simulate a login to retrieve a token
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Use token to access the /user/me/ endpoint
    response = client.get(
        "/user/me/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == test_user_data["username"]
    assert "user_id" in user_data
    assert user_data["autoreply_timeout"] is None or isinstance(user_data["autoreply_timeout"], int)


# Test updating user settings with valid data
def test_update_user_settings_success():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    new_settings = {
        "autoreply_timeout": 120
    }

    # Update settings for the current user
    response = client.patch(
        "/user/me/",
        json=new_settings,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    updated_user_data = response.json()
    assert updated_user_data["email"] == test_user_data["username"]
    assert updated_user_data["autoreply_timeout"] == new_settings["autoreply_timeout"]


@pytest.mark.parametrize("invalid_timeout", [-1, 86401, "invalid"])
def test_update_user_settings_invalid_timeout(invalid_timeout):
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    response = client.patch(
        "/user/me/",
        json={"autoreply_timeout": invalid_timeout},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_get_user_me_unauthorized():
    response = client.get("/user/me/")
    assert response.status_code == 401  # Unauthorized
    assert response.json() == {"detail": "Not authenticated"}


def test_update_user_settings_unauthorized():
    response = client.patch("/user/me/", json={"autoreply_timeout": 1200})
    assert response.status_code == 401  # Unauthorized
    assert response.json() == {"detail": "Not authenticated"}


# Test retrieving all posts
def test_get_all_posts():
    response = client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert isinstance(posts, list)
    if posts:
        assert "title" in posts[0]
        assert "body" in posts[0]
        assert "author_id" in posts[0]


# Test creating a new post successfully
def test_create_new_post():
    # Authenticate to get a token
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    new_post_data = {
        "title": "Test Post Title",
        "body": "This is the body of the test post."
    }

    # Create a new post
    response = client.post(
        "/posts/",
        json=new_post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    post = response.json()
    assert post["title"] == new_post_data["title"]
    assert post["body"] == new_post_data["body"]
    assert post["author_id"] == 1  # Assuming this is the test user's ID


# Test fetching a single post by ID
def test_get_post_by_id():
    # Insert a test post if not already created in previous tests
    test_post_data = {
        "title": "Another Test Post Title",
        "body": "This is another test post body."
    }
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Create the post to ensure it exists
    post_response = client.post(
        "/posts/",
        json=test_post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["post_id"]

    # Fetch the post by ID
    response = client.get(f"/posts/{post_id}/")
    assert response.status_code == 200
    post = response.json()
    assert post["post_id"] == post_id
    assert post["title"] == test_post_data["title"]
    assert post["body"] == test_post_data["body"]


# Test fetching a non-existent post by ID
def test_get_nonexistent_post():
    response = client.get("/posts/9999/")  # Assuming ID 9999 does not exist
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


# Test editing a post successfully
def test_edit_post():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Create a new post for editing
    new_post_data = {
        "title": "Edit Test Post Title",
        "body": "This is a post body to edit."
    }
    post_response = client.post(
        "/posts/",
        json=new_post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    post_id = post_response.json()["post_id"]

    updated_post_data = {
        "title": "Updated Post Title",
        "body": "This is the updated body of the post."
    }

    # Edit the post
    response = client.patch(
        f"/posts/{post_id}/",
        json=updated_post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    updated_post = response.json()
    assert updated_post["title"] == updated_post_data["title"]
    assert updated_post["body"] == updated_post_data["body"]


# Test editing a post without authorization
def test_edit_post_unauthorized():
    # Attempt to edit a post without authentication
    response = client.patch(
        "/posts/1/",
        json={"title": "Should not work", "body": "Unauthorized edit attempt"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test editing a post that belongs to another user
def test_edit_other_user_post():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Assuming there’s a post created by a different user with ID 9999
    response = client.patch(
        "/posts/4/",
        json={"title": "Unauthorized Edit", "body": "Editing another user's post"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Access forbidden"}


# Test retrieving all comments for a post
def test_get_comments_to_post():
    post_id = 1  # Assuming post with ID 1 exists
    response = client.get(f"/comments/by_post/{post_id}")
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)
    if comments:
        assert "body" in comments[0]
        assert "author_id" in comments[0]
        assert "post_id" in comments[0]
        assert comments[0]["post_id"] == post_id


# Test adding a comment to a post
def test_add_comment_to_post():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    post_id = 1  # Assuming post with ID 1 exists
    comment_data = {
        "body": "This is a new comment on post 1."
    }

    response = client.post(
        f"/comments/by_post/{post_id}",
        json=comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    comment = response.json()
    assert comment["body"] == comment_data["body"]
    assert comment["post_id"] == post_id
    assert comment["author_id"] == 1  # Assuming this is the test user's ID


# Test retrieving all comments by an author
def test_get_comments_by_author():
    author_id = 1  # Assuming user with ID 1 exists
    response = client.get(f"/comments/by_author/{author_id}")
    assert response.status_code == 200
    comments = response.json()
    assert isinstance(comments, list)
    if comments:
        assert comments[0]["author_id"] == author_id


# Test retrieving a specific comment by ID
def test_get_comment_by_id():
    comment_id = 1  # Assuming comment with ID 1 exists
    response = client.get(f"/comments/{comment_id}")
    assert response.status_code == 200
    comment = response.json()
    assert comment["comment_id"] == comment_id
    assert "body" in comment
    assert "author_id" in comment


# Test replying to a comment
def test_reply_to_comment():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    parent_comment_id = 1  # Assuming comment with ID 1 exists
    reply_data = {
        "body": "This is a reply to comment 1."
    }

    response = client.post(
        f"/comments/{parent_comment_id}/reply",
        json=reply_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    reply_comment = response.json()
    assert reply_comment["body"] == reply_data["body"]
    assert reply_comment["reply_to"] == parent_comment_id


# Test replying to a comment that is already a reply (should fail)
def test_reply_to_reply_comment():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Create a new comment to serve as a parent reply
    post_id = 1
    initial_comment_data = {
        "body": "Initial comment that will be replied to."
    }
    initial_comment_response = client.post(
        f"/comments/by_post/{post_id}",
        json=initial_comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    initial_comment_id = initial_comment_response.json()['comment_id']

    # Create a reply to the initial comment
    reply_data = {
        "body": "This is a reply to the initial comment."
    }
    reply_comment_response = client.post(
        f"/comments/{initial_comment_id}/reply",
        json=reply_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    reply_comment_id = reply_comment_response.json()['comment_id']

    # Attempt to reply to the comment that is already a reply
    response = client.post(
        f"/comments/{reply_comment_id}/reply",
        json={"body": "This should not be allowed"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "This comment cannot be replied"}


# Test editing a comment successfully
def test_edit_comment():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Create a new comment for editing
    post_id = 1
    new_comment_data = {
        "body": "Comment to be edited."
    }
    comment_response = client.post(
        f"/comments/by_post/{post_id}",
        json=new_comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    comment_id = comment_response.json()["comment_id"]

    # Edit the comment
    updated_comment_data = {
        "body": "This is the edited comment."
    }
    response = client.patch(
        f"/comments/{comment_id}/",
        json=updated_comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    edited_comment = response.json()
    assert edited_comment["body"] == updated_comment_data["body"]


# Test editing a comment that has replies (should fail)
def test_edit_comment_with_replies():
    response = client.post(
        "/auth/token",
        data=test_user_data
    )
    token = response.json()["access_token"]

    # Create a new comment and a reply to it
    post_id = 1
    comment_data = {"body": "Original comment with reply"}
    comment_response = client.post(
        f"/comments/by_post/{post_id}",
        json=comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    comment_id = comment_response.json()["comment_id"]

    # Add a reply to this comment
    reply_data = {"body": "Reply to original comment"}
    client.post(
        f"/comments/{comment_id}/reply",
        json=reply_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Attempt to edit the original comment (should fail)
    updated_comment_data = {"body": "Edited comment"}
    response = client.patch(
        f"/comments/{comment_id}/",
        json=updated_comment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 418
    assert response.json() == {"detail": "Comment is already replied"}
