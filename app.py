from flask import Flask, request, render_template, jsonify
import logging, time, uuid, threading, sys, os, json, argparse

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = "your-secret-key"

parser = argparse.ArgumentParser(description="Run the Flask registration server.")
parser.add_argument(
    '--config', 
    default = 'config_example.json',
    help = 'Path to the JSON config file'
)
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config_data = json.load(f)

settings = config_data["settings"]  # UI + technical settings
groups_raw = config_data["groups"]
groups = {}
for group_item in groups_raw:
    group_id = group_item["id"]
    name = group_item["name"]
    slots = group_item["slots"]
    desc = group_item.get("description", "")

    groups[group_id] = {
        "name": name,
        "description": desc,
        "capacity": slots,  # current available
        "total": slots,
        "slots_string": f"{slots}/{slots} wolnych miejsc",
        "registered": []
    }

# Sets for name/email/cookie-based duplicates
used_names = set()
used_emails = set()
used_ids = set()  # Store the "unique_id" cookie values here

active_users = {}  # key = cookie_id, value = last request timestamp (float)

# SINGLE RATE for both client poll + server timeout
refresh_rate_ms = settings.get("refresh_rate_ms", 2000)  # default 5s
server_timeout_seconds = refresh_rate_ms / 1000.0        # convert ms -> s

# UTILITY FUNCTIONS
def save_registrations(filename="registrations.txt"):
    """
    Write the current group data and who registered to a file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        for group_name, data in groups.items():
            f.write(f"Group {group_name} (Capacity left: {data['capacity']}/{data['total']}):\n")
            for (name, email, _) in data["registered"]:
                f.write(f"{name} - {email}\n")
            f.write("\n")
    print(f"Registrations saved to {filename}")

def exit_on_enter():
    """
    Wait for the user to press Enter in the console.
    Then save registrations and exit.
    """
    input("Press Enter to finish and stop the server...\n")
    print("Shutting down...")
    save_registrations()
    os._exit(0)

# HOOKS before / after request
@app.before_request
def track_by_cookie():
    """
    1) Identify this user by cookie (if they have one).
    2) Track them as "active" if they do have a cookie.
    3) Clean up old entries (inactive > ACTIVE_VISITOR_TIMEOUT).
    4) Log the request, including how many are active.
    """
    user_cookie = request.cookies.get('unique_id')

    # Clean out old users
    now = time.time()
    for cookie_val, last_time in list(active_users.items()):
        if now - last_time > server_timeout_seconds:
            del active_users[cookie_val]

    # If the user *already* has a cookie, update their "last seen" time
    if user_cookie:
        active_users[user_cookie] = now

    # Log it. If no cookie yet, user_cookie is None
    app.logger.info(
        f"\n[REQUEST]\nCookie ID: {user_cookie if user_cookie else 'NO_COOKIE'}, "
        f"Active Visitors ~ {len(active_users)}\n"
    )

@app.after_request
def set_unique_cookie(response):
    """
    If the user doesn't have 'unique_id' cookie yet, generate one and set it.
    Done after the route's logic so the cookie is in the final response.
    """
    if not request.cookies.get('unique_id'):
        new_id = str(uuid.uuid4())
        # For example, set it for 1 year (max_age=31536000 seconds).
        response.set_cookie('unique_id', new_id, max_age=31536000)
    return response

# MAIN ROUTES
@app.route('/', methods=['GET', 'POST'])
def index():
    error_msg = None
    success_msg = None

    # Retrieve the cookie ID, if it exists
    user_cookie = request.cookies.get('unique_id')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        chosen_group = request.form.get('group')

        registration_status = "Failed"
        # If user_cookie is None, it means they're brand new
        if not user_cookie:
            error_msg = "Brak unikalnego identyfikatora. Odśwież stronę i spróbuj ponownie."
        elif name in used_names:
            error_msg = f"Imię '{name}' jest już zarejestrowane!"
        elif email in used_emails:
            error_msg = f"E-mail '{email}' jest już zarejestrowany!"
        elif user_cookie in used_ids:
            error_msg = "Możliwa jest tylko jedna rejestracja!"
        elif chosen_group not in groups:
            error_msg = f"Grupa '{chosen_group}' nie istnieje!"
        else:
            # Capacity check
            if groups[chosen_group]["capacity"] > 0:
                groups[chosen_group]["capacity"] -= 1
                groups[chosen_group]["registered"].append((name, email, user_cookie))
                groups[chosen_group]["slots_string"] = \
                    f"{groups[chosen_group]["capacity"]}/{groups[chosen_group]["total"]} wolnych miejsc" \
                    if groups[chosen_group]["capacity"] > 0 else "Brak wolnych miejsc"

                used_names.add(name)
                used_emails.add(email)
                used_ids.add(user_cookie)

                success_msg = f"Udało się zapisać do grupy {chosen_group}!"
                registration_status = "Success"
            else:
                error_msg = f"{groups[chosen_group]["name"]} jest już pełna. Spróbuj ponownie."

        # --- CUSTOM LOGGING for POST ---
        curr_state = "\n    ".join(
            f"Group {grp}: {data['capacity']}/{data['total']}"
            for grp, data in groups.items()
        )
        app
        if registration_status == "Success":
            app.logger.info(
                f"\n[SUCCESS]\n  name = '{name}'\n  email = '{email}'"
                f"\n  IP = {user_cookie}\n  group = {chosen_group}\n"
                f"  Current state:\n    {curr_state}\n"
            )
        else:
            app.logger.info(
                f"\n[FAILURE]\n  name = '{name}'\n  email = '{email}'\n  IP = {user_cookie}\n"
                f"  group = {chosen_group or 'Unknown'}\n  reason = '{error_msg}'\n"
                f"  Current state:\n    {curr_state}\n"
            )
        # --- END CUSTOM LOGGING ---

    return render_template(
        'index.html',
        groups = groups,
        settings = settings,
        error_msg = error_msg,
        success_msg = success_msg
    )

@app.route('/get_data', methods=['GET'])
def get_data():
    capacity_data = {}
    registration_data = {}

    for group_id, info in groups.items():
        # 1) Build capacity info
        capacity_data[group_id] = {
            "capacity": info["capacity"],
            "total": info["total"]
        }

        # 2) Build registration info
        registrants_list = []
        for (n, e, _) in info["registered"]:
            registrants_list.append({"name": n, "email": e})

        registration_data[group_id] = {
            "group_name": info["name"],
            "registrants": registrants_list
        }

    # Return everything in one JSON response
    return jsonify({
        "capacity_data": capacity_data,
        "registration_data": registration_data
    })
# MAIN ENTRY POINT
if __name__ == "__main__":
    # Start background thread that waits for Enter
    thread = threading.Thread(target=exit_on_enter, daemon=True)
    thread.start()

    # 4) Run without debug or reloader
    #    so there's only ONE process to kill
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
