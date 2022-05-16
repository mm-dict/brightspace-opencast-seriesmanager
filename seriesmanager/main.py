
from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal
from .core.exc import SeriesManagerError
from .controllers.base import Base
from .controllers.courses import Courses
from .controllers.series import Series
from .controllers.schedules import Schedules
from .controllers.cleanupseries import CleanupSeries

import d2lvalence.auth as d2lauth

from tinydb import TinyDB
from cement.utils import fs
import os

# configuration defaults
CONFIG = init_defaults('opencast','bs')
# CONFIG['bs']['user_creds'] = {'user_id': 'xhp8oC-Y6DzMsuRIXA7bV9', 'user_key': 'FPHeBsYdZ0uo9Tk4crUf1K'}
# CONFIG['bs']['app_creds'] = {'app_id': 'MOu_08G8hpYxU5Cr_Vyq4A', 'app_key': '_Sc2PNxdev99yIzHtlZ9lA'}
# CONFIG['bs']['courses_endpoint'] = 'https://uforaqas.ugent.be/d2l/api/lp/1.9/orgstructure/?orgUnitType=3'
# CONFIG['bs']['host'] = 'uforaqas.ugent.be'

def extend_d2l_uc(app):
    app.log.debug('extending SeriesManager application with D2L user context')

    s = d2lauth.D2LSigner()
    uc = d2lauth.D2LUserContext(app.config.get('bs','host'),
            user_id = app.config.get('bs','user_creds')['user_id'],
            user_key = app.config.get('bs','user_creds')['user_key'],
            app_id = app.config.get('bs','app_creds')['app_id'],
            app_key = app.config.get('bs','app_creds')['app_key'],
            encrypt_requests = True,
            signer = s)

    app.log.debug('using user id : ' + app.config.get('bs','user_creds')['user_id'])

    app.extend('d2l_uc',uc)

def extend_tinydb(app):
    app.log.debug('extending SeriesManager application with OpenCast series DB file')
    db_file = app.config.get('opencast', 'db_file')

    # ensure that we expand the full path
    db_file = fs.abspath(db_file)
    app.log.debug('tinydb database file is: %s' % db_file)

    # ensure our parent directory exists
    db_dir = os.path.dirname(db_file)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    app.extend('oc_db', TinyDB(db_file))

class SeriesManager(App):
    """Ufora OpenCast Series Manager primary application."""

    class Meta:
        label = 'seriesmanager'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base,
            Courses,
            Series,
            Schedules,
            CleanupSeries
        ]

        hooks = [
            ('post_setup', extend_d2l_uc),
            ('post_setup', extend_tinydb),
        ]

class SeriesManagerTest(TestApp,SeriesManager):
    """A sub-class of SeriesManager that is better suited for testing."""

    class Meta:
        label = 'seriesmanager'


def main():
    with SeriesManager() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except SeriesManagerError as e:
            print('SeriesManagerError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
