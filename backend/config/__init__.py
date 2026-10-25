"""Database driver selection.

Django's MySQL/MariaDB backend expects the ``MySQLdb`` module. ``mysqlclient`` provides it but
needs a C compiler on Windows/macOS, so when it is not installed we fall back to the pure-Python
PyMySQL driver (listed in requirements.txt), which installs everywhere with no build tools.
"""
USING_PYMYSQL = False
try:
    import MySQLdb  # noqa: F401  (mysqlclient)
except ImportError:
    try:
        import pymysql
        pymysql.version_info = (2, 2, 7, "final", 0)  # satisfies Django's minimum driver version check
        pymysql.install_as_MySQLdb()
        USING_PYMYSQL = True
    except ImportError:  # SQLite-only development works without either driver
        pass
