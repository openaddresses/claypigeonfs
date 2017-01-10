import os, TileStache, ModestMaps
from flask import Flask, Response
from .tippecanoe import Config

app = Flask(__name__)
config = Config('.')

@app.route('/<int:zoom>/<int:col>/<int:row>.<ext>')
@app.route('/<int:zoom>/<int:col>/<int:row>')
def get_tile(zoom, col, row, ext='json'):
    layer = config.layers['dots.mbtiles']
    coord = ModestMaps.Core.Coordinate(row, col, zoom) # (1582, 656, 12)
    mime, body = TileStache.getTile(layer, coord, ext)
    return Response(body, headers={'Content-Type': mime})
