# DO NOT MODIFY THIS FORK

This is a cloned fork of [pyftpdlib v1.5.9](https://pypi.org/project/pyftpdlib/1.5.9/) with parts removed to avoid crash loops within Kodi.

If you need to update for _any_ reason proceed to download the pyftpdlib source and replace the module here.
Secondly, remove all of the classes related to `Threaded` behaviors in `pyftpdlib` as they're the source of a crash loop.