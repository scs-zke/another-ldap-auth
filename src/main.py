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
if "LDAP_ENDPOINT" in os.environ:
    LDAP_ENDPOINT = os.environ["LDAP_ENDPOINT"]

if "LDAP_MANAGER_DN_USERNAME" in os.environ:
    LDAP_MANAGER_DN_USERNAME = os.environ["LDAP_MANAGER_DN_USERNAME"]

if "LDAP_MANAGER_PASSWORD" in os.environ:
    LDAP_MANAGER_PASSWORD = os.environ["LDAP_MANAGER_PASSWORD"]

if "LDAP_SEARCH_BASE" in os.environ:
    LDAP_SEARCH_BASE = os.environ["LDAP_SEARCH_BASE"]

if "LDAP_SEARCH_FILTER" in os.environ:
    LDAP_SEARCH_FILTER = os.environ["LDAP_SEARCH_FILTER"]

# Ldap user attribute specifying the groups the user is a member of
LDAP_GROUP_MEMBERSHIP_ATTRIBUTE = "memberOf"
if "LDAP_GROUP_MEMBERSHIP_ATTRIBUTE" in os.environ:
    LDAP_GROUP_MEMBERSHIP_ATTRIBUTE = os.environ["LDAP_GROUP_MEMBERSHIP_ATTRIBUTE"]

# List of users separated by comma
LDAP_ALLOWED_USERS = ""
if "LDAP_ALLOWED_USERS" in os.environ:
    LDAP_ALLOWED_USERS = os.environ["LDAP_ALLOWED_USERS"]

# List of groups separated by comma
LDAP_ALLOWED_GROUPS = ""
if "LDAP_ALLOWED_GROUPS" in os.environ:
    LDAP_ALLOWED_GROUPS = os.environ["LDAP_ALLOWED_GROUPS"]

# The default is "and", another option is "or"
LDAP_ALLOWED_GROUPS_CONDITIONAL = "and"
if "LDAP_ALLOWED_GROUPS_CONDITIONAL" in os.environ:
    LDAP_ALLOWED_GROUPS_CONDITIONAL = os.environ["LDAP_ALLOWED_GROUPS_CONDITIONAL"]
if LDAP_ALLOWED_GROUPS_CONDITIONAL not in ["or", "and"]:
    raise ValueError(f"LDAP_ALLOWED_GROUPS_CONDITIONAL '{LDAP_ALLOWED_GROUPS_CONDITIONAL}' not allowed")

# The default is "enabled", another option is "disabled"
LDAP_ALLOWED_GROUPS_CASE_SENSITIVE = True
if "LDAP_ALLOWED_GROUPS_CASE_SENSITIVE" in os.environ:
    LDAP_ALLOWED_GROUPS_CASE_SENSITIVE = os.environ["LDAP_ALLOWED_GROUPS_CASE_SENSITIVE"] == "enabled"

# The default is "or", another option is "and"
LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL = "or"
if "LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL" in os.environ:
    LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL = os.environ["LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL"]
if LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL not in ["or", "and"]:
    raise ValueError(f"LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL '{LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL}' not allowed")

# Bind DN for the LDAP connection, supports variable expansion for {username}
LDAP_BIND_DN = "{username}"
if "LDAP_BIND_DN" in os.environ:
    LDAP_BIND_DN = os.environ["LDAP_BIND_DN"]

# List of required configuration headers separated by comma
NGINX_REQUIRED_CONFIG_HEADERS = ""
if "NGINX_REQUIRED_CONFIG_HEADERS" in os.environ:
    NGINX_REQUIRED_CONFIG_HEADERS = os.environ["NGINX_REQUIRED_CONFIG_HEADERS"]

# Key for encrypt the Session
FLASK_SECRET_KEY = "".join(secrets.choice(string.ascii_letters + string.digits) for i in range(64)).encode("utf8")
if "FLASK_SECRET_KEY" in os.environ:
    FLASK_SECRET_KEY = str(os.environ["FLASK_SECRET_KEY"]).encode("utf8")

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

        def check_n_follow_link(fname, max_recursion=10):
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

    # Get configuration from request headers
    try:
        ldap_endpoint = LDAP_ENDPOINT
        if "Ldap-Endpoint" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Endpoint" in request.headers:
                if request.headers["Ldap-Endpoint"] != "":
                    ldap_endpoint = request.headers["Ldap-Endpoint"]
            else:
                logs.error({"message": "Ldap-Endpoint header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_manager_dn_username = LDAP_MANAGER_DN_USERNAME
        if "Ldap-Manager-Dn-Username" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Manager-Dn-Username" in request.headers:
                if request.headers["Ldap-Manager-Dn-Username"] != "":
                    ldap_manager_dn_username = request.headers["Ldap-Manager-Dn-Username"]
            else:
                logs.error({"message": "Ldap-Manager-Dn-Username header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_manager_password = LDAP_MANAGER_PASSWORD
        if "Ldap-Manager-Password" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Manager-Password" in request.headers:
                if request.headers["Ldap-Manager-Password"] != "":
                    ldap_manager_password = request.headers["Ldap-Manager-Password"]
            else:
                logs.error({"message": "Ldap-Manager-Password header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_bind_dn = LDAP_BIND_DN
        if "Ldap-Bind-DN" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Bind-DN" in request.headers:
                if request.headers["Ldap-Bind-DN"] != "":
                    ldap_bind_dn = request.headers["Ldap-Bind-DN"]
            else:
                logs.error({"message": "Ldap-Bind-DN header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_search_base = LDAP_SEARCH_BASE
        if "Ldap-Search-Base" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Search-Base" in request.headers:
                if request.headers["Ldap-Search-Base"] != "":
                    ldap_search_base = request.headers["Ldap-Search-Base"]
            else:
                logs.error({"message": "Ldap-Search-Base header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_search_filter = LDAP_SEARCH_FILTER
        if "Ldap-Search-Filter" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Search-Filter" in request.headers:
                if request.headers["Ldap-Search-Filter"] != "":
                    ldap_search_filter = request.headers["Ldap-Search-Filter"]
            else:
                logs.error({"message": "Ldap-Search-Filter header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_group_membership_attribute = LDAP_GROUP_MEMBERSHIP_ATTRIBUTE
        if "Ldap-Group-Membership-Attribute" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Group-Membership-Attribute" in request.headers:
                if request.headers["Ldap-Group-Membership-Attribute"] != "":
                    ldap_group_membership_attribute = request.headers["Ldap-Group-Membership-Attribute"]
            else:
                logs.error({"message": "Ldap-Group-Membership-Attribute header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_allowed_users = LDAP_ALLOWED_USERS
        if "Ldap-Allowed-Users" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Allowed-Users" in request.headers:
                if request.headers["Ldap-Allowed-Users"] != "":
                    ldap_allowed_users = request.headers["Ldap-Allowed-Users"]
            else:
                logs.error({"message": "Ldap-Allowed-Users header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_allowed_groups = LDAP_ALLOWED_GROUPS
        if "Ldap-Allowed-Groups" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Allowed-Groups" in request.headers:
                if request.headers["Ldap-Allowed-Groups"] != "":
                    ldap_allowed_groups = request.headers["Ldap-Allowed-Groups"]
            else:
                logs.error({"message": "Ldap-Allowed-Groups header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_allowed_groups_case_sensitive = LDAP_ALLOWED_GROUPS_CASE_SENSITIVE
        if "Ldap-Allowed-Groups-Case-Sensitive" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Allowed-Groups-Case-Sensitive" in request.headers:
                if request.headers["Ldap-Allowed-Groups-Case-Sensitive"] != "":
                    ldap_allowed_groups_case_sensitive = request.headers["Ldap-Allowed-Groups-Case-Sensitive"] == "enabled"
            else:
                logs.error(
                    {"message": "Ldap-Allowed-Groups-Case-Sensitive header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."}
                )
                return False

        ldap_allowed_groups_conditional = LDAP_ALLOWED_GROUPS_CONDITIONAL
        if "Ldap-Allowed-Groups-Conditional" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Allowed-Groups-Conditional" in request.headers:
                if request.headers["Ldap-Allowed-Groups-Conditional"] != "":
                    ldap_allowed_groups_conditional = request.headers["Ldap-Allowed-Groups-Conditional"]
                if ldap_allowed_groups_conditional not in ["and", "or"]:
                    logs.error(
                        {
                            "message": "Invalid conditional for groups matching.",
                            "username": username,
                            "conditional": ldap_allowed_groups_conditional,
                        }
                    )
                    return False
            else:
                logs.error({"message": "Ldap-Allowed-Groups-Conditional header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."})
                return False

        ldap_allowed_groups_users_conditional = LDAP_ALLOWED_GROUPS_USERS_CONDITIONAL
        if "Ldap-Allowed-Groups-Users-Conditional" in NGINX_REQUIRED_CONFIG_HEADERS.split(","):
            if "Ldap-Allowed-Groups-Users-Conditional" in request.headers:
                if request.headers["Ldap-Allowed-Groups-Users-Conditional"] != "":
                    ldap_allowed_groups_users_conditional = request.headers["Ldap-Allowed-Groups-Users-Conditional"]
                if ldap_allowed_groups_users_conditional not in ["or", "and"]:
                    logs.error(
                        {
                            "message": "Invalid conditional for groups and user matching.",
                            "username": username,
                            "conditional": ldap_allowed_groups_users_conditional,
                        }
                    )
                    return False
            else:
                logs.error(
                    {"message": "Ldap-Allowed-Groups-Users-Conditional header specified in NGINX_REQUIRED_CONFIG_HEADERS but not recieved in auth request."}
                )
                return False

        # Restrict users and groups if restriction headers are set
        if "Ldap-User-Restrictions" in request.headers:
            restricted_users = set(request.headers["Ldap-User-Restrictions"].split(","))
            allowed_users = set(ldap_allowed_users.split(","))
            ldap_allowed_users = ",".join(list(allowed_users.intersection(restricted_users)))

        if "Ldap-Group-Restrictions" in request.headers:
            restricted_groups = set(request.headers["Ldap-Group-Restrictions"].split(","))
            allowed_groups = set(ldap_allowed_groups.split(","))
            ldap_allowed_groups = ",".join(list(allowed_groups.intersection(restricted_groups)))

    except KeyError as e:
        logs.error({"message": f"Invalid parameters. {e}"})
        return False

    if not ldap_allowed_users and not ldap_allowed_groups:
        logs.error({"message": "Neither LDAP_ALLOWED_USERS nor LDAP_ALLOWED_GROUPS has been specified. Unable to authenticate any users."})
        return False

    aldap = Aldap(
        ldap_endpoint,
        ldap_manager_dn_username,
        ldap_manager_password,
        ldap_bind_dn,
        ldap_search_base,
        ldap_search_filter,
        ldap_group_membership_attribute,
        ldap_allowed_groups_case_sensitive,
        ldap_allowed_groups_conditional,
        LDAP_TLS_CA_CERT_FILE,
    )

    cache.settings(ldap_allowed_groups_case_sensitive, ldap_allowed_groups_conditional)

    # Check if the username and password are valid
    # First check inside the cache and then in the LDAP server
    if not cache.validateUser(username, password):
        if aldap.authenticateUser(username, password):
            cache.addUser(username, password)
        else:
            bruteForce.addFailure()
            return False

    # Validate user via matching users
    if ldap_allowed_users:
        matchingUsers = ldap_allowed_users.split(",")  # Convert string to list
        matchingUsers = list(map(cleanMatchingUsers, matchingUsers))
        if username in matchingUsers:
            logs.info(
                {
                    "message": "Username inside the allowed users list.",
                    "username": username,
                    "matchingUsers": ",".join(matchingUsers),
                }
            )
            if ldap_allowed_groups_users_conditional == "or":
                setRegister(username, [])
                return True
        elif not ldap_allowed_groups or ldap_allowed_groups_users_conditional == "and":
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
    if ldap_allowed_groups:
        matchingGroups = ldap_allowed_groups.split(",")  # Convert string to list
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

        options = {"bind": f"0.0.0.0:{PORT}", "workers": NUMBER_OF_WORKERS, "threads": 1, "timeout": 5}

        if RELOAD_ENABLED and RELOAD_EXTRA_FILES:
            options.update(
                {
                    "preload_app": False,
                    "reload": True,
                    # hard coded to poll2, our slightly improved version of Reloader
                    # because of inotify problems with NFS and
                    # we need to follow links in case of mounted secrets/configmaps in kubernetes
                    "reload_engine": "poll2",
                    "reload_extra_files": RELOAD_EXTRA_FILES,
                }
            )
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
