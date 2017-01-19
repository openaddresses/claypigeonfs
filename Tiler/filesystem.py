#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
lltest.py - Example file system for Python-LLFUSE.

This program presents a static file system containing a single file. It is
compatible with both Python 2.x and 3.x. Based on an example from Gerion Entrup.

Copyright © 2015 Nikolaus Rath <Nikolaus.org>
Copyright © 2015 Gerion Entrup.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
from argparse import ArgumentParser

import os
import sys
import stat
import logging
import errno
import struct
import base64
import hashlib
import urllib.parse

import llfuse
from . import remote

try:
    import faulthandler
except ImportError:
    pass
else:
    faulthandler.enable()

log = logging.getLogger(__name__)

class RemoteFileFS(llfuse.Operations):
    '''
    '''
    def __init__(self, base_url, *args, **kwargs):
        llfuse.Operations.__init__(self, *args, **kwargs)
        self.base_url = base_url
        self.inode_map = dict()

    def getattr(self, inode, ctx=None):
        log.debug('RemoteFileFS.getattr: {}, {}'.format(inode, ctx))

        entry = llfuse.EntryAttributes()

        if inode == llfuse.ROOT_INODE:
            entry.st_mode = (stat.S_IFDIR | 0o755)
            entry.st_size = 0
        elif inode in self.inode_map:
            try:
                entry.st_mode = (stat.S_IFREG | 0o644)
                entry.st_size = get_remote_file_object(self.inode_map[inode]).length
            except Exception as e:
                log.error('%s in RemoteFileFS.gettatr: %s', type(e), e)
                raise llfuse.FUSEError(errno.EIO)
        else:
            raise llfuse.FUSEError(errno.ENOENT)

        stamp = int(1438467123.985654 * 1e9)
        entry.st_atime_ns = stamp
        entry.st_ctime_ns = stamp
        entry.st_mtime_ns = stamp
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode

        return entry

    def lookup(self, parent_inode, name, ctx=None):
        log.debug('RemoteFileFS.lookup: {}, {}, {}'.format(parent_inode, name, ctx))
        
        if parent_inode != llfuse.ROOT_INODE:
            raise llfuse.FUSEError(errno.ENOENT)

        try:
            hash_inode, full_url = calculate_file_inode(name, self.base_url)
        except Exception as e:
            log.error('%s in RemoteFileFS.lookup: %s', type(e), e)
            raise llfuse.FUSEError(errno.ENOENT)

        self.inode_map[hash_inode] = full_url
        return self.getattr(hash_inode)

    def open(self, inode, flags, ctx):
        log.debug('RemoteFileFS.open: {}, {}, {}'.format(inode, flags, ctx))
        if inode not in self.inode_map:
            raise llfuse.FUSEError(errno.ENOENT)
        if flags & os.O_RDWR or flags & os.O_WRONLY:
            raise llfuse.FUSEError(errno.EPERM)
        return inode

    def read(self, inode, off, size):
        log.debug('RemoteFileFS.read: {}, {}, {}'.format(inode, off, size))

        if inode not in self.inode_map:
            raise llfuse.FUSEError(errno.ENOENT)

        try:
            file = get_remote_file_object(self.inode_map[inode])
            file.seek(off)
            data = file.read(size)
        except Exception as e:
            log.error('%s in RemoteFileFS.read: %s', type(e), e)
            raise llfuse.FUSEError(errno.EIO)

        return data

def calculate_file_inode(name_bytes, base_url):
    ''' Calculate and return inode number and full URL for file name.
    
        File name is interpreted as base64-encoded bytes and joined to base URL.
    '''
    rel_name = base64.b64decode(name_bytes).decode('utf8')
    full_url = urllib.parse.urljoin(base_url, rel_name)
    log.debug('rel_name: {}, full_url: {}'.format(rel_name, full_url))

    hashed = hashlib.sha1(full_url.encode('utf8'))
    (hash_inode, ) = struct.unpack('L', hashed.digest()[:8])
    log.debug('hashed: {}, hash_inode: {}'.format(hashed.hexdigest(), hash_inode))
    
    if urllib.parse.urlparse(full_url).scheme not in ('http', 'https'):
        raise ValueError('Unknown URL scheme in {}'.format(repr(full_url)))
    
    if base_url and not full_url.startswith(base_url):
        raise ValueError('URL outside of {}: {}'.format(base_url, repr(full_url)))
    
    return hash_inode, full_url

def get_remote_file_object(url):
    ''' Return remote.RemoteFileObject() instance for a URL.
    '''
    return remote.RemoteFileObject(url, verbose=True, block_size=256*1024)

def init_logging(debug=False):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(threadName)s: '
                                  '[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

def parse_args():
    ''' Parse command line.
    '''
    parser = ArgumentParser()

    parser.add_argument('mountpoint', type=str,
                        help='Where to mount the file system')
    parser.add_argument('--base-url', type=str,
                        help='Base URL under which all file names will be found.')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False,
                        help='Enable FUSE debugging output')
    return parser.parse_args()


def main():
    options = parse_args()
    init_logging(options.debug)

    remotefs = RemoteFileFS(options.base_url)
    fuse_options = set(llfuse.default_options)
    fuse_options.add('fsname=Tiler.filesystem')
    if options.debug_fuse:
        fuse_options.add('debug')
    llfuse.init(remotefs, options.mountpoint, fuse_options)
    try:
        llfuse.main(workers=1)
    except:
        llfuse.close(unmount=False)
        raise

    llfuse.close()

if __name__ == '__main__':
    main()
