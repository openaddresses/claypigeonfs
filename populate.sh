for SHP in mtn_view/*.shp; do
	shp2pgsql -dD $SHP | psql openaddr
done

for SHP in cupertino/*.shp; do
	shp2pgsql -dD $SHP | psql openaddr
done
