import atexit
import json
from shutil import rmtree

import better_exceptions
from zenlog import log

from manga_py.cli import args
from manga_py.libs import fs
from manga_py.libs.db import Manga, make_db
from manga_py.libs.modules import info
from ._helper import CliHelper


class Cli(CliHelper):
    def __init__(self):
        self._temp_path = fs.get_temp_path()
        atexit.register(self.exit)
        fs.make_dirs(self._temp_path)
        self.global_info = info.InfoGlobal()

    def exit(self):
        # remove temp directory
        rmtree(self._temp_path)

    def run(self):
        better_exceptions.hook()
        _args = self._args.copy()
        self._print_cli_help()
        urls = _args.get('url', []).copy()
        make_db(force=_args.get('force_make_db', False))
        if self._args.get('update_all'):
            self._update_all()
        else:
            if len(urls) > 1:
                _args['name'] = None
                _args['skip_volumes'] = None
                _args['max_volumes'] = None
            self._run_normal(_args, urls)

    def _update_all(self):
        db = Manga()
        default_args = self.get_default_args()
        for manga in db.select():
            log.info('Update %s', manga.url)
            _args = default_args.copy()
            """
            :var manga Manga
            """
            data = json.loads(manga.data)
            data_args = data.get('args', {})
            del data_args['rewrite_exists_archives']
            del data_args['user_agent']
            _args.update({  # re-init args
                'url': manga.url,
                **data_args,
            })
            provider = self._get_provider(_args)
            provider.http.cookies = data.get('cookies')
            provider.http.ua = data.get('browser')
            provider.run(_args)
            self.global_info.add_info(info)
            manga.update()  # TODO

    def _run_normal(self, _args, urls):
        for url in urls:
            manga = Manga()
            _args['url'] = url
            provider = self._get_provider(_args)
            provider.run(_args)
            self.global_info.add_info(info)
            manga.update()  # TODO
