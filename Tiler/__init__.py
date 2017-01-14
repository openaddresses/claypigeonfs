import os, TileStache, ModestMaps
from flask import Flask, Response, render_template
from .tippecanoe import Config

app = Flask(__name__)
config = Config('.')

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/scene.yaml')
def get_scene():
    return Response(render_template('scene.yaml'),
        headers={'Content-Type': 'application/x-yaml'})

@app.route('/<int:zoom>/<int:col>/<int:row>.<ext>')
@app.route('/<int:zoom>/<int:col>/<int:row>')
def get_tile(zoom, col, row, ext='json'):
    layer = config.layers['/tmp/dotmaps/dots.mbtiles']
    coord = ModestMaps.Core.Coordinate(row, col, zoom) # (1582, 656, 12)
    mime, body = TileStache.getTile(layer, coord, ext)
    headers = {'Content-Type': mime}
    if ext == 'mvt':
        headers.update({'Content-Encoding': 'gzip'})
    return Response(body, headers=headers)
