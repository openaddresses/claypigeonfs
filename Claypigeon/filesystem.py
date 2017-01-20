#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Remote (HTTP) FUSE filesystem. Exposes getattr, lookup, open, read, and release
methods. Accepts base64-encoded relative and absolute URLs as filenames, and
exposes raw bytes backed by HTTP range requests to minimize network overhead.

Adapted from:

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
import base64
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
    def __init__(self, base_url, block_size, *args, **kwargs):
        llfuse.Operations.__init__(self, *args, **kwargs)
        self.base_url = base_url
        self.block_size = block_size
        self.inode_list = [None for i in range(llfuse.ROOT_INODE + 1)]
        self.open_files = dict()

    def getattr(self, inode, ctx=None):
        log.debug('RemoteFileFS.getattr: {}, {}'.format(inode, ctx))

        entry = llfuse.EntryAttributes()

        if inode == llfuse.ROOT_INODE:
            entry.st_mode = (stat.S_IFDIR | 0o755)
            entry.st_size = 0
        elif inode < len(self.inode_list):
            try:
                entry.st_mode = (stat.S_IFREG | 0o644)
                entry.st_size = remote.RemoteFileObject(self.inode_list[inode], block_size=self.block_size).length
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
            full_url = calculate_file_url(name, self.base_url)
        except Exception as e:
            log.error('%s in RemoteFileFS.lookup: %s', type(e), e)
            raise llfuse.FUSEError(errno.ENOENT)

        if full_url in self.inode_list:
            inode = self.inode_list.index(full_url)
            log.debug('RemoteFileFS.lookup: found {} at {}'.format(full_url, inode))
        else:
            inode = len(self.inode_list)
            log.debug('RemoteFileFS.lookup: added {} at {}'.format(full_url, inode))
            self.inode_list.append(full_url)
        
        return self.getattr(inode)

    def open(self, inode, flags, ctx):
        log.debug('RemoteFileFS.open: {}, {}, {}'.format(inode, flags, ctx))

        if inode >= len(self.inode_list):
            raise llfuse.FUSEError(errno.ENOENT)

        if flags & os.O_RDWR or flags & os.O_WRONLY:
            raise llfuse.FUSEError(errno.EPERM)

        try:
            self.open_files[inode] = remote.RemoteFileObject(self.inode_list[inode], block_size=self.block_size)
        except Exception as e:
            log.error('%s in RemoteFileFS.open: %s', type(e), e)
            raise llfuse.FUSEError(errno.EIO)
        
        return inode

    def read(self, inode, off, size):
        log.debug('RemoteFileFS.read: {}, {}, {}'.format(inode, off, size))

        if inode >= len(self.inode_list) or inode not in self.open_files:
            raise llfuse.FUSEError(errno.ENOENT)

        try:
            self.open_files[inode].seek(off)
            data = self.open_files[inode].read(size)
        except Exception as e:
            log.error('%s in RemoteFileFS.read: %s', type(e), e)
            raise llfuse.FUSEError(errno.EIO)

        return data
    
    def release(self, inode):
        log.debug('RemoteFileFS.release: {}'.format(inode))
        del self.open_files[inode]

def calculate_file_url(name_bytes, base_url):
    ''' Calculate and return a full URL for file name.
    
        File name is interpreted as base64-encoded bytes and joined to base URL.
    '''
    rel_name = base64.b64decode(name_bytes).decode('utf8')
    full_url = urllib.parse.urljoin(base_url, rel_name)
    log.debug('rel_name: {}, full_url: {}'.format(rel_name, full_url))

    if urllib.parse.urlparse(full_url).scheme not in ('http', 'https'):
        raise ValueError('Unknown URL scheme in {}'.format(repr(full_url)))
    
    if base_url and not full_url.startswith(base_url):
        raise ValueError('URL outside of {}: {}'.format(base_url, repr(full_url)))
    
    return full_url

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
    parser.add_argument('--block-size', type=int, default=256*1024,
                        help='Block size in bytes for remote file object. Default 256KB.')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False,
                        help='Enable FUSE debugging output')
    return parser.parse_args()


def main():
    options = parse_args()
    init_logging(options.debug)

    remotefs = RemoteFileFS(options.base_url, options.block_size)
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
