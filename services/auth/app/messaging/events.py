# Channel names untuk Redis Pub/Sub
# Format: <service>.<entity>.<action>

USER_REGISTERED  = "auth.user.registered"   # payload: user_id, username, email, role
USER_LOGGED_IN   = "auth.user.logged_in"    # payload: user_id, username
USER_LOGGED_OUT  = "auth.user.logged_out"   # payload: user_id
