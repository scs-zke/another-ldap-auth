# pylint: disable=missing-docstring

import os
import platform
import secrets
import string

from flask import Flask
from flask import request
from flask import g
from flask_httpauth import HTTPBasicAuth

import gunicorn.app.base
import gunicorn.reloader

from aldap import Aldap
from bruteforce import BruteForce
from cache import Cache
from logs import Logs

# --- Parameters --------------------------------------------------------------
# Key for encrypt the Session
FLASK_SECRET_KEY = "".join(secrets.choice(string.ascii_letters + string.digits) for i in range(64)).encode('utf8')
if "FLASK_SECRET_KEY" in os.environ:
    FLASK_SECRET_KEY = str(os.environ["FLASK_SECRET_KEY"]).encode('utf8')

# Cache expiration in minutes
CACHE_EXPIRATION = 5
if "CACHE_EXPIRATION" in os.environ:
    CACHE_EXPIRATION = int(os.environ["CACHE_EXPIRATION"])

# Brute force enable or disable
BRUTE_FORCE_PROTECTION = False
if "BRUTE_FORCE_PROTECTION" in os.environ:
    BRUTE_FORCE_PROTECTION = os.environ["BRUTE_FORCE_PROTECTION"] == "enabled"

# Brute force expiration in seconds
BRUTE_FORCE_EXPIRATION = 10
if "BRUTE_FORCE_EXPIRATION" in os.environ:
    BRUTE_FORCE_EXPIRATION = int(os.environ["BRUTE_FORCE_EXPIRATION"])

# Brute force amount of failures
BRUTE_FORCE_FAILURES = 3
if "BRUTE_FORCE_FAILURES" in os.environ:
    BRUTE_FORCE_FAILURES = int(os.environ["BRUTE_FORCE_FAILURES"])

# Use gunicorn as WSGI server
USE_WSGI_SERVER = True
if "USE_WSGI_SERVER" in os.environ and os.environ["USE_WSGI_SERVER"].lower() in ("0", "false", "n", "no", "off"):
    USE_WSGI_SERVER = False

# Enable or disable reload API
RELOAD_ENABLED = False
RELOAD_EXTRA_FILES = []
if "RELOAD_ENABLED" in os.environ and os.environ["RELOAD_ENABLED"].lower() in ("1", "true", "y", "yes", "on"):
    RELOAD_ENABLED = True

# Enable or disable TLS self-signed certificate without WSGI server
TLS_ENABLED = False
if "TLS_ENABLED" in os.environ and os.environ["TLS_ENABLED"].lower() in ("1", "true", "y", "yes", "on"):
    TLS_ENABLED = True

# TLS key and certificate WSGI server
if TLS_ENABLED and USE_WSGI_SERVER:
    if "TLS_KEY_FILE" in os.environ:
        TLS_KEY_FILE = os.environ["TLS_KEY_FILE"]
        if RELOAD_ENABLED:
            RELOAD_EXTRA_FILES.append(TLS_KEY_FILE)
    else:
        raise ValueError("TLS_KEY_FILE must be set when using TLS and WSGI server")

    if "TLS_CERT_FILE" in os.environ:
        TLS_CERT_FILE = os.environ["TLS_CERT_FILE"]
        if RELOAD_ENABLED:
            RELOAD_EXTRA_FILES.append(TLS_CERT_FILE)
    else:
        raise ValueError("TLS_CERT_FILE must be set when using TLS and WSGI server")

    if "TLS_CA_CERT_FILE" in os.environ:
        TLS_CA_CERT_FILE = os.environ["TLS_CA_CERT_FILE"]
        if RELOAD_ENABLED:
            RELOAD_EXTRA_FILES.append(TLS_CA_CERT_FILE)
    else:
        TLS_CA_CERT_FILE = None

# TLS ca-certificates for LDAP connection
LDAP_TLS_CA_CERT_FILE = None
if "LDAP_TLS_CA_CERT_FILE" in os.environ:
    LDAP_TLS_CA_CERT_FILE = os.environ["LDAP_TLS_CA_CERT_FILE"]
    if RELOAD_ENABLED:
        RELOAD_EXTRA_FILES.append(LDAP_TLS_CA_CERT_FILE)

# Number of gunicorn workers
# Should be 1 because of credentials caching
NUMBER_OF_WORKERS = 1
if "NUMBER_OF_WORKERS" in os.environ:
    NUMBER_OF_WORKERS = int(os.environ["NUMBER_OF_WORKERS"])

PORT = 9000
if "PORT" in os.environ:
    PORT = int(os.environ["PORT"])


# --- Functions ---------------------------------------------------------------
class UpdatedReloader(gunicorn.reloader.Reloader):

    def __init__(self, extra_files=None, interval=10, callback=None):
        super().__init__(extra_files, interval, callback)

    def get_files(self):

        def check_n_follow_link(fname, max_recursion = 10):
            r = max_recursion
            fn = fname

            if not os.path.islink(fn):
                return fn

            while r > 0:
                r -= 1
                fn = os.readlink(fn)

                if not os.path.islink(fn):
                    return fn

            raise Exception(f"Too many recursions. Can't follow linked file '{fname}'.")

        return [check_n_follow_link(fn) for fn in self._extra_files]


def cleanMatchingUsers(item: str):
    item = item.strip()
    item = item.lower()
    return item


def cleanMatchingGroups(item: str):
    item = item.strip()
    return item


def setRegister(username: str, matchedGroups: list):
    g.username = username
    g.matchedGroups = ",".join(matchedGroups)


def getRegister(key):
    return g.get(key)


# --- Logging -----------------------------------------------------------------
logs = Logs("main")

# --- Cache -------------------------------------------------------------------
cache = Cache(CACHE_EXPIRATION)

# --- Brute Force -------------------------------------------------------------
bruteForce = BruteForce(BRUTE_FORCE_PROTECTION, BRUTE_FORCE_EXPIRATION, BRUTE_FORCE_FAILURES)

# --- Flask -------------------------------------------------------------------
app = Flask(__name__)
auth = HTTPBasicAuth()


@auth.verify_password
def login(username, password):
    if not username or not password:
        logs.error({"message": "Username or password empty."})
        return False

    if bruteForce.isIpBlocked():
        return False

    try:
        if "Ldap-Endpoint" in request.headers:
            LDAP_ENDPOINT = request.headers.get("Ldap-Endpoint")
        else:
            LDAP_ENDPOINT = os.environ["LDAP_ENDPOINT"]

        if "Ldap-Manager-Dn-Username" in request.headers:
            LDAP_MANAGER_DN_USERNAME = request.headers["Ldap-Manager-Dn-Username"]
        else:
            LDAP_MANAGER_DN_USERNAME = os.environ["LDAP_MANAGER_DN_USERNAME"]

        if "Ldap-Manager-Password" in request.headers:
            LDAP_MANAGER_PASSWORD = request.headers["Ldap-Manager-Password"]
        else:
            LDAP_MANAGER_PASSWORD = os.environ["LDAP_MANAGER_PASSWORD"]

        if "Ldap-Search-Base" in request.headers:
            LDAP_SEARCH_BASE = request.headers["Ldap-Search-Base"]
        else:
            LDAP_SEARCH_BASE = os.environ["LDAP_SEARCH_BASE"]

        if "Ldap-Search-Filter" in request.headers:
            LDAP_SEARCH_FILTER = request.headers["Ldap-Search-Filter"]
        else:
            LDAP_SEARCH_FILTER = os.environ["LDAP_SEARCH_FILTER"]

        # List of groups separated by comma
        LDAP_ALLOWED_GROUPS = ""
        if "Ldap-Allowed-Groups" in request.headers:
            LDAP_ALLOWED_GROUPS = request.headers["Ldap-Allowed-Groups"]
        elif "LDAP_ALLOWED_GROUPS" in os.environ:
            LDAP_ALLOWED_GROUPS = os.environ["LDAP_ALLOWED_GROUPS"]

        # The default is "and", another option is "or"
        LDAP_ALLOWED_GROUPS_CONDITIONAL = "and"
        if "Ldap-Allowed-Groups-Conditional" in request.headers:
            LDAP_ALLOWED_GROUPS_CONDITIONAL = request.headers["Ldap-Allowed-Groups-Conditional"]
        elif "LDAP_ALLOWED_GROUPS_CONDITIONAL" in os.environ:
            LDAP_ALLOWED_GROUPS_CONDITIONAL = os.environ["LDAP_ALLOWED_GROUPS_CONDITIONAL"]

        # The default is "enabled", another option is "disabled"
        LDAP_ALLOWED_GROUPS_CASE_SENSITIVE = True
        if "Ldap-Allowed-Groups-Case-Sensitive" in request.headers:
            LDAP_ALLOWED_GROUPS_CASE_SENSITIVE = request.headers["Ldap-Allowed-Groups-Case-Sensitive"] == "enabled"
        elif "LDAP_ALLOWED_GROUPS_CASE_SENSITIVE" in os.environ:
            LDAP_ALLOWED_GROUPS_CASE_SENSITIVE = os.environ["LDAP_ALLOWED_GROUPS_CASE_SENSITIVE"] == "enabled"

        # List of users separated by comma
        LDAP_ALLOWED_USERS = ""
        if "Ldap-Allowed-Users" in request.headers:
            LDAP_ALLOWED_USERS = request.headers["Ldap-Allowed-Users"]
        elif "LDAP_ALLOWED_USERS" in os.environ:
            LDAP_ALLOWED_USERS = os.environ["LDAP_ALLOWED_USERS"]

        # The default is "or", another option is "and"
        LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL = "or"
        if "Ldap-Allowed-Groups-Users-Conditional" in request.headers:
            LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL = request.headers["Ldap-Allowed-Groups-Users-Conditional"]
        elif "LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL" in os.environ:
            LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL = os.environ["LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL"]
        if LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL not in ["or", "and"]:
            logs.error(
                {
                    "message": "Invalid conditional for groups and user matching.",
                    "username": username,
                    "conditional": LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL,
                }
            )
            return False

        LDAP_BIND_DN = "{username}"
        if "Ldap-Bind-DN" in request.headers:
            LDAP_BIND_DN = request.headers["Ldap-Bind-DN"]
        elif "LDAP_BIND_DN" in os.environ:
            LDAP_BIND_DN = os.environ["LDAP_BIND_DN"]
    except KeyError as e:
        logs.error({"message": f"Invalid parameters. {e}"})
        return False

    aldap = Aldap(
        LDAP_ENDPOINT,
        LDAP_MANAGER_DN_USERNAME,
        LDAP_MANAGER_PASSWORD,
        LDAP_BIND_DN,
        LDAP_SEARCH_BASE,
        LDAP_SEARCH_FILTER,
        LDAP_ALLOWED_GROUPS_CASE_SENSITIVE,
        LDAP_ALLOWED_GROUPS_CONDITIONAL,
        LDAP_TLS_CA_CERT_FILE,
    )

    cache.settings(LDAP_ALLOWED_GROUPS_CASE_SENSITIVE, LDAP_ALLOWED_GROUPS_CONDITIONAL)

    # Check if the username and password are valid
    # First check inside the cache and then in the LDAP server
    if not cache.validateUser(username, password):
        if aldap.authenticateUser(username, password):
            cache.addUser(username, password)
        else:
            bruteForce.addFailure()
            return False

    # Validate user via matching users
    if LDAP_ALLOWED_USERS:
        matchingUsers = LDAP_ALLOWED_USERS.split(",")  # Convert string to list
        matchingUsers = list(map(cleanMatchingUsers, matchingUsers))
        if username in matchingUsers:
            logs.info(
                {
                    "message": "Username inside the allowed users list.",
                    "username": username,
                    "matchingUsers": ",".join(matchingUsers),
                }
            )
            if LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL == "or":
                setRegister(username, [])
                return True
        elif not LDAP_ALLOWED_GROUPS or LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL == "and":
            logs.info(
                {
                    "message": "Username not found inside the allowed users list.",
                    "username": username,
                    "matchingUsers": ",".join(matchingUsers),
                }
            )
            return False

    # Validate user via matching groups
    matchedGroups = []
    if LDAP_ALLOWED_GROUPS:
        matchingGroups = LDAP_ALLOWED_GROUPS.split(",")  # Convert string to list
        matchingGroups = list(map(cleanMatchingGroups, matchingGroups))
        validGroups, matchedGroups = cache.validateGroups(username, matchingGroups)
        if not validGroups:
            validGroups, matchedGroups, adGroups = aldap.validateGroups(username, matchingGroups)
            if not validGroups:
                return False
            else:
                cache.addGroups(username, adGroups)

    # Success
    setRegister(username, matchedGroups)
    return True


# Health-Check URL
@app.route("/healthz", defaults={"path": "/healthz"})
def healthz(path):  # pylint: disable=unused-argument
    code = 200
    msg = "OK"
    return msg, code


# Catch-All URL
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
@auth.login_required
def index(path):  # pylint: disable=unused-argument
    code = 200
    msg = "Another LDAP Auth"
    headers = [
        ("x-username", getRegister("username")),
        ("x-groups", getRegister("matchedGroups")),
    ]
    return msg, code, headers


# Overwrite response
@app.after_request
def remove_header(response):
    # Change "Server:" header to avoid display server properties
    response.headers["Server"] = ""
    return response


# Main
if __name__ == "__main__":
    app.secret_key = FLASK_SECRET_KEY

    if USE_WSGI_SERVER and platform.uname().system.lower() == "linux":

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, g_app, g_options=None):
                self.options = g_options or {}
                self.application = g_app
                super().__init__()

            def init(self, parser, opts, args):
                pass

            def load_config(self):
                config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            "bind": f"0.0.0.0:{PORT}",
            "workers": NUMBER_OF_WORKERS,
            "threads": 1,
            "timeout": 5
        }

        if RELOAD_ENABLED and RELOAD_EXTRA_FILES:
            options.update({
                "preload_app": False,
                "reload": True,
                # hard coded to poll2, our slightly improved version of Reloader
                # because of inotify problems with NFS and
                # we need to follow links in case of mounted secrets/configmaps in kubernetes
                "reload_engine" : "poll2",
                "reload_extra_files": RELOAD_EXTRA_FILES
            })
            gunicorn.reloader.reloader_engines["poll2"] = UpdatedReloader

        if TLS_ENABLED:
            options["keyfile"] = TLS_KEY_FILE  # pylint: disable=possibly-used-before-assignment
            options["certfile"] = TLS_CERT_FILE  # pylint: disable=possibly-used-before-assignment
        if TLS_ENABLED and TLS_CA_CERT_FILE:  # pylint: disable=possibly-used-before-assignment
            options["ca_certs"] = TLS_CA_CERT_FILE

        StandaloneApplication(app, options).run()
    else:
        print("Detected non Linux, Running in pure Flask")
        if TLS_ENABLED:
            app.run(host="0.0.0.0", port=PORT, debug=False, ssl_context="adhoc")
        else:
            app.run(host="0.0.0.0", port=PORT, debug=False)
