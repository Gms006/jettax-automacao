import sys


def check_package(name):
    try:
        module = __import__(name)
        version = getattr(module, "__version__", "unknown")
        print(f"{name} OK: {version}")
    except Exception as exc:
        print(f"{name} ERROR: {exc}")


def main():
    print("Python version:", sys.version)
    for package in ("requests", "pandas"):
        check_package(package)


if __name__ == "__main__":
    main()
