from logger import log
HOST_ROLE = 0
GUEST_ROLE = 1


# Validates the username for special characters, length, and more
# Returns true/false and logs the reason why requests were denied
def ValidateUsername(username, role, users, changing_host, request):
    global HOST_ROLE
    global GUEST_ROLE

    roleText = "guest"
    if (role == HOST_ROLE):
        roleText = "host"

    logMessage = "Received " + roleText + " request with requested username '" + username + "'. "

    # Verify username is not greater than 20 characters
    if (len(username) > 20):
        log(logMessage + "Denied for reason: username too long", request)
        return { "value": False, "reason": "username_too_long" }

    # Check if username contains disallowed characters
    elif ("<" in username or ">" in username or "(" in username or ")" in username):
        log(logMessage + "Denied for reason: username contained special characters that are not allowed", request)
        return { "value": False, "reason": "username_special_characters" }

    # Check if username is blank
    elif (username == ""):
        log(logMessage + "Denied for reason: username was blank", request)
        return { "value": False, "reason": "username_blank" }

    # Check if username was already taken
    else:
        success_joining = True
        if (not changing_host):
            for user in users:
                if users[user]["username"] == username:
                    success_joining = False

        if (not success_joining):
            log(logMessage + "Denied for reason: username was already taken", request)
            return { "value": False, "reason": "username_not_unique" }
        else:
            log(logMessage + "Request approved.", request)
            return { "value": True }