# auth.py
import keyring
import typer
import webbrowser
from pathlib import Path

SERVICE_NAME = "aye-cli"
TOKEN_ENV_VAR = "AYE_TOKEN"
TOKEN_FILE = Path.home() / ".ayecfg"


def store_token(token: str) -> None:
    """Persist the token in ~/.ayecfg (unless AYE_TOKEN is set)."""
    try:
        TOKEN_FILE.write_text(token.strip(), encoding="utf-8")
        TOKEN_FILE.chmod(0o600)  # POSIX only
    except Exception:
        typer.echo("⚠️  Failed to write to config file. Falling back to keyring.")
        keyring.set_password(SERVICE_NAME, "user-token", token)


def get_token() -> str | None:
    """Return the stored token (env → file → keyring fallback)."""
    # 1. Try environment variable first
    env_token = typer.getenv(TOKEN_ENV_VAR)
    if env_token:
        return env_token.strip()

    # 2. Try config file
    if TOKEN_FILE.is_file():
        try:
            return TOKEN_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass  # Continue to keyring if file read fails

    # 3. Fall back to keyring
    try:
        token = keyring.get_password(SERVICE_NAME, "user-token")
        if token:
            return token
    except Exception:
        pass

    return None


def delete_token() -> None:
    """Delete the token from file and keyring (but not environment)."""
    # Delete the file-based token
    TOKEN_FILE.unlink(missing_ok=True)

    # Delete from keyring (ignore if missing)
    try:
        keyring.delete_password(SERVICE_NAME, "user-token")
    except Exception:
        pass


def login_flow() -> None:
    """
    Small login flow:
    1. Prompt user to obtain token at https://aye.acrotron.com
    2. User enters/pastes the token in terminal (hidden input)
    3. Save the token to ~/.ayecfg (if AYE_TOKEN not set)
    """
    typer.echo(
        "Aye uses a token-only login. Obtain your token at https://aye.acrotron.com"
    )
    token = typer.prompt("Paste your token", hide_input=True)
    store_token(token.strip())
    typer.secho("✅ Token saved.", fg=typer.colors.GREEN)
