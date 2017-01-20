Claypigeon is a read-only FUSE filesystem for remote ranged HTTP files. It is
designed to allow filesystem access to remote files over HTTP, such as SQLite
databases too large to download quickly.

Install on Ubuntu Linux:

    apt-get install pkg-config libfuse-dev python3-dev libattr1-dev
    pip install Claypigeon

Use:

    claypigeon-mount --base-url http://example.com /mnt

Help:

    claypigeon-mount --help
