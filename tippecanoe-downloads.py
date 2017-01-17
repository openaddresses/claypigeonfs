import sys, csv, zipfile, os, itertools, io, json, tempfile, subprocess

OA_PROPERTIES = 'HASH', 'NUMBER', 'STREET', 'UNIT', 'CITY', 'POSTCODE'

with open('downloaded/files.csv') as file:
    run_rows = csv.DictReader(file)
    
    set_key = lambda run_row: int(run_row['set_id'])
    sorted_rows = sorted(run_rows, key=set_key, reverse=False)
    grouped_rows = itertools.groupby(sorted_rows, set_key)
    
    for (set_id, runs) in grouped_rows:
        print('Starting set', set_id, '...', file=sys.stderr)
        
        mbtiles_filename = 'set_{}.mbtiles'.format(set_id)
        cmd = 'tippecanoe', '-l', 'dots', '-r', '3', \
              '-n', 'OpenAddresses Dots, Set {}'.format(set_id), '-f', \
              '-t', tempfile.gettempdir(), '-o', mbtiles_filename
    
        print(' '.join(cmd), file=sys.stderr)
        tippecanoe = subprocess.Popen(cmd, stdin=subprocess.PIPE, bufsize=1)
        
        for run_row in runs:
            data_path = os.path.join('downloaded', run_row['path'])
            _, data_ext = os.path.splitext(data_path)
            
            if data_ext == '.csv':
                csv_buff = open(data_path)

            elif data_ext == '.zip':
                zip = zipfile.ZipFile(data_path)
                (csv_name, ) = [name for name in zip.namelist()
                                if os.path.splitext(name)[1] == '.csv']

                csv_buff = io.TextIOWrapper(zip.open(csv_name))

            for csv_row in csv.DictReader(csv_buff):
                try:
                    x, y = float(csv_row['LON']), float(csv_row['LAT'])
                except ValueError:
                    continue
                else:
                    geometry = dict(type='Point', coordinates=[x, y])

                properties = {key.lower(): csv_row.get(key, '') for key in OA_PROPERTIES}
                properties.update(source_path=run_row['source_path'])
                feature = dict(type='Feature', geometry=geometry, properties=properties)
                tippecanoe.stdin.write(json.dumps(feature).encode('utf8'))
                tippecanoe.stdin.write(b'\n')
                #break

        tippecanoe.stdin.close()
        tippecanoe.wait()
        
        #break
