# Number of worker processes Gunicorn will spawn.
# A common recommendation is (2 * number_of_cpu_cores) + 1.
# '4' is a reasonable default.
workers = 4

# The address and port Gunicorn will listen on.
# '0.0.0.0' means listen on all available network interfaces.
# '8000' is the port number.
bind = '0.0.0.0:8000'

# The level of detail for logging.
# Options include 'debug', 'info', 'warning', 'error', 'critical'.
# 'info' is a good default for production.
loglevel = 'info'