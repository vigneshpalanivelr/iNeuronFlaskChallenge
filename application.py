"""
Main Entry point of the script
"""
import sys
from apps import create_app
from apps.config import config_dict

configuration_mode = 'Production'

try:
    app_config = config_dict[configuration_mode]
    print()
except KeyError:
    sys.exit(f'Error: Invalid Configuration mode: {configuration_mode}')

application = create_app(app_config)
app = application
# app.jinja_env.globals.update(zip=zip)
# app.jinja_env.globals.update(enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True)
