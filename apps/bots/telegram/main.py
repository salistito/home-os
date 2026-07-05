from core.db import init_db


def main() -> None:
    init_db()
    print("HomeOS up. DB lista.")


if __name__ == "__main__":
    main()
