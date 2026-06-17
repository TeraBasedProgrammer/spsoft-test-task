from dotenv import load_dotenv

# Load the environment variables first to ensure
# they are available to the imported modules
load_dotenv(".env")

from livekit.agents import cli  # noqa: E402

from . import sessions  # noqa: F401, E402  # pyright: ignore[reportUnusedImport]
from .server import server  # noqa: E402


def main():
    cli.run_app(server)


if __name__ == "__main__":
    main()
