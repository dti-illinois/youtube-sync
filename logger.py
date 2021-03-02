import datetime
import os

if not os.path.exists('logs'):
    os.makedirs('logs')

# The log file name
LOG_FILE_NAME = datetime.datetime.now().strftime("./logs/log_%G%m%d_%H%M%S.log")


# Logs data to the console and the log file
def log(message, webRequest = None):
    global users

    if (webRequest is None):
        log_string = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "]: " + message + "\n"
    else:
        ip_string = ""
        sid_string = ""
        username_string = "]: "

        try:
            if (webRequest.remote_addr is not None):
                ip_string = "[" + webRequest.remote_addr
            if (webRequest.sid is not None):
                sid_string = ", " + webRequest.sid + ""
                username_string = ", " + users[webRequest.sid]["username"] + "]: "
        except:
            pass

        log_string = "[" + datetime.datetime.now().strftime(
            "%H:%M:%S") + "] " + ip_string + sid_string + username_string + message + "\n"
    print(log_string)
    with open(LOG_FILE_NAME, 'a') as log_file:
        log_file.write(log_string)