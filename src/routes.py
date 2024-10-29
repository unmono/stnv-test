from fastapi import APIRouter


user_router = APIRouter(
    prefix="/user",
)

@user_router.get("/{user_id}/")
def user_space(user_id: int):
    pass

@user_router.patch("/{user_id}/")
def update_user_settings(user_id: int):
    pass

@user_router.get("/{user_id}/posts/")
def user_posts(user_id: int):
    pass

@user_router.get("/{user_id}/comments/")
def user_comments(user_id: int):
    pass


posts_router = APIRouter(
    prefix="/posts",
)

@posts_router.get("/")
def posts_list():
    pass

@posts_router.post("/")
def new_post():
    pass

@posts_router.get("/{post_id}/")
def get_post(post_id: int):
    pass

@posts_router.patch("/{post_id}/")
def edit_post(post_id: int):
    pass

@posts_router.delete("/{post_id}/")
def delete_post(post_id: int):
    pass

@posts_router.get("/{post_id}/comments/")
def post_comments(post_id: int):
    pass

@posts_router.post("/{post_id}/comments/")
def comment_post(post_id: int):
    pass


comments_router = APIRouter(
    prefix="/comments",
)

@comments_router.get("/{comment_id}/")
def get_comment(comment_id: int):
    pass

@comments_router.patch("/{comment_id}/")
def edit_comment(comment_id: int):
    pass

@comments_router.delete("/{comment_id}/")
def delete_comment(comment_id: int):
    pass

@comments_router.post("/{comment_id}/reply/")
def reply_comment(comment_id: int):
    pass
