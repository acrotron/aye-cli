import keyring
import typer
import webbrowser

SERVICE_NAME = "aye-cli"
TOKEN_ENV_VAR = "AYE_TOKEN"


def store_token(token: str) -> None:
    """Persist the token securely in the OS keyring."""
    keyring.set_password(SERVICE_NAME, "user-token", token)


def get_token() -> str | None:
    """Return the stored token, or None if not present."""
    token = keyring.get_password(SERVICE_NAME, "user-token")
    if not token:
        token = typer.getenv(TOKEN_ENV_VAR)   # optional env‑var fallback
    return token


def delete_token() -> None:
    """Remove the token from the keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, "user-token")
    except keyring.errors.PasswordDeleteError:
        pass


def login_flow(callback_url: str) -> None:
    """
    Very small login flow:
    1. Open a browser to `callback_url`.
    2. The user copies the one‑time token displayed there.
    3. Paste the token into the terminal; we store it.
    """
    typer.echo(
        "Aye uses a token‑only login. A page will open – copy the token and paste it."
    )
    webbrowser.open(callback_url)
    token = typer.prompt("Paste your token")
    store_token(token.strip())
    typer.secho("✅ Token saved.", fg=typer.colors.GREEN)


