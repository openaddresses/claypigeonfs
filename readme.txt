http://web.archive.org/web/20070227082525/http://fdo.osgeo.org/files/fdo/docs/FDG_FDODevGuide/files/WS7106c181349dd8d016672d6105df83c6e7-7fff.htm

    While geometry typically is two- or three-dimensional, it may also contain
    the measurement dimension (M) to provide the basis for dynamic segments.

http://postgis.17.x6.nabble.com/4D-points-td3598428.html

    'm' is 'measure' an extra axis of information not associated with the
    cartesian x/y/z space. The most common use for 'measure' is actually for
    'measurements', the adding of physically known measurements about a feature
    to the abstract 'feature' represented in x/y space in the GIS. For example,
    highway management systems often understand the location of facilities in
    terms of 'mile posts'. So, in addition to x/y coordinates, each vertex is
    also assigned a 'mile' measurement in 'm' which allows the system to
    accurately place facility information relative to the 'milepost' system.
    (Why not just use the x/y coordinates and calculate distances off of them?
    Because they are representational, the distances calculated from the x/y
    will not be the same as the actual milepost measurements.) 

source .vrt files could go to:

1.  PostGIS for whole-earth tile storage
2.  MBTiles for per-run slippy maps
