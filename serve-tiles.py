import os, TileStache, ModestMaps
from flask import Flask, Response

app = Flask(__name__)

config = TileStache.Config.buildConfiguration({
    "cache": {"name": "Test"},
    "layers": {
        "dots": {
            "provider": {
                "class": "tiler:TippecanoeProvider",
                "kwargs": {"path": "dots.mbtiles"}
                }
            }
        }
    }, '.')

@app.route('/<int:zoom>/<int:col>/<int:row>.<ext>')
@app.route('/<int:zoom>/<int:col>/<int:row>')
def get_tile(zoom, col, row, ext='json'):
    layer = config.layers['dots']
    coord = ModestMaps.Core.Coordinate(row, col, zoom) # (1582, 656, 12)
    mime, body = TileStache.getTile(layer, coord, ext)
    return Response(body, headers={'Content-Type': mime})

if __name__ == '__main__':
    app.run(debug=True)
