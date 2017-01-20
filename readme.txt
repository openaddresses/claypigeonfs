Claypigeon is a FUSE filesystem for remote ranged HTTP files. It is designed to
allow filesystem access to remote files over HTTP, such as SQLite databases too
large to download quickly.

Install:

    pip install Claypigeon

Use:

    claypigeon-mount --base-url http://example.com /mnt

Help:

    claypigeon-mount --help
