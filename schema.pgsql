CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;

-- Name: dots; Type: TABLE; Schema: public; Owner: migurski; Tablespace: 

CREATE TABLE dots (
    source_path character varying,
    run_id integer,
    hash character varying,
    number character varying,
    street character varying,
    unit character varying,
    postcode character varying,
    geom geometry,
    CONSTRAINT enforce_dims_geom CHECK ((st_ndims(geom) = 3)),
    CONSTRAINT enforce_geotype_geom CHECK (((geometrytype(geom) = 'POINTM'::text) OR (geom IS NULL))),
    CONSTRAINT enforce_srid_geom CHECK ((st_srid(geom) = 4326))
);

-- Name: dots_nd_index; Type: INDEX; Schema: public; Owner: migurski; Tablespace: 

CREATE INDEX dots_nd_index ON dots USING gist (geom gist_geometry_ops_nd);
