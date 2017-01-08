from os.path import relpath
import sqlite3, subprocess, re

WARNING_PAT_TPL = r'^\S+: Warning: using tile \d+/\d+/\d+ instead of {0}/{1}/{2}\n'

class TippecanoeProvider:
    ''' Accepts requests for tiles from a Tippecanoe MBTiles file.
    '''
    def __init__(self, layer, path):
        self.path = relpath(path, layer.config.dirpath)
    
    def renderTile(self, width, height, srs, coord):
        ''' Return a TileWriter instance for a single tile.
        '''
        if coord.zoom <= 14:
            return TileWriter(self.path, coord)
        else:
            raise ValueError('Out of range TippecanoeProvider zoom {}'.format(coord.zoom))
    
    def getTypeByExtension(self, extension):
        if extension.lower() == 'mvt':
            return ('application/x-protobuf', 'Mapbox Vector Tile')
        elif extension.lower() in ('geojson', 'json'):
            return ('application/json', 'GeoJSON')
        else:
            raise ValueError('Unknown TippecanoeProvider extension {}'.format(extension))

class TileWriter:
    ''' Requests and serializes a single tile from a Tippecanoe MBTiles file.
    '''
    def __init__(self, path, coord):
        self.path = path
        self.coord = coord
        self.zxy = self.coord.zoom, self.coord.column, self.coord.row
    
    def save(self, output, format):
        if format == 'Mapbox Vector Tile':
            return self.save_MapboxVectorTile(output)
        elif format == 'GeoJSON':
            return self.save_GeoJSON(output)
        else:
            raise ValueError('Unknown TileWriter format {}'.format(format))
    
    def save_MapboxVectorTile(self, output):
        ''' Write raw MVT bytes from MBTiles row to output.
        '''
        with sqlite3.connect(self.path) as db:
            tile_row = (2**self.coord.zoom - 1) - self.coord.row
            res = db.execute('''
                SELECT tile_data FROM tiles
                WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
                ''', (self.coord.zoom, self.coord.column, tile_row))
            try:
                (content, ) = res.fetchone()
            except TypeError:
                raise ValueError('Missing TileWriter tile {}/{}/{}'.format(*self.zxy))
        output.write(content)
    
    def save_GeoJSON(self, output):
        ''' Write GeoJSON bytes from tippecanoe-decode to output.
        '''
        z, x, y = self.zxy
        command = 'tippecanoe-decode', self.path, str(z), str(x), str(y)
        content = subprocess.check_output(command, stderr=subprocess.STDOUT)
        heading = content[:256].decode('utf8', 'ignore') # should be on line 1
        if 'Warning' in heading:
            warning_pattern = re.compile(WARNING_PAT_TPL.format(*self.zxy))
            if warning_pattern.match(heading):
                raise ValueError('Missing TileWriter tile {}/{}/{}'.format(*self.zxy))
        output.write(content)
