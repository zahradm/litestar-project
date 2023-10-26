from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.security.session_auth import SessionAuth
from litestar.middleware.session.server_side import ServerSideSessionBackend, ServerSideSessionConfig

from handlers import (
    login,
    signup,
    get_user,
    add_note,
    update_note,
    delete_note,
    get_note,
    retrieve_user_handler
)
from models import User

openapi_config = OpenAPIConfig(title="My API", version="1.0.0")

session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    session_backend_config=ServerSideSessionConfig(),
    exclude=["/login", "/signup", "/note/{note_id}"],
)

app = Litestar(
    route_handlers=[login, signup, get_user, add_note, update_note, delete_note, get_note],
    on_app_init=[session_auth.on_app_init],
    openapi_config=openapi_config,
)
