import sys, glob, psycopg2, urllib.parse, os, csv
from os.path import relpath, join, dirname

_, DB_DSN = sys.argv

with psycopg2.connect(DB_DSN) as conn:
    with conn.cursor() as db:
        db.execute('''
            CREATE TEMPORARY TABLE run_urls
            AS SELECT id, set_id, source_path, (state->'processed')::text AS url
            FROM runs
            WHERE state IS NOT NULL
              AND state::text != 'null'
              AND set_id IN (-63331, -54733, -44438, -36544, -27542, -20088,
              -13308, -1963, 18859, 24465, 30562, 43050, 52181, 58315, 65703,
              73276, 80311, 85697, 92640, 100816, 108487, 115738, 123450,
              131277, 141476)
            ''')
    
        with open('downloaded/files.csv', 'w') as file:
            rows = csv.DictWriter(file, ('run_id', 'set_id', 'source_path', 'url', 'path'))
            rows.writeheader()
            
            for meta_path in glob.glob('downloaded/*/URL.txt'):
                with open(meta_path) as file:
                    data_url, data_path = next(file).strip(), next(file).strip()
            
                    parsed_url = urllib.parse.urlparse(data_url)
                
                    db.execute('''
                        SELECT id, set_id, source_path
                        FROM run_urls
                        WHERE url LIKE %s
                        ''',
                        ('%{}"'.format(parsed_url.path), ))
                
                    local_path = relpath(join(dirname(meta_path), data_path), 'downloaded')

                    for (run_id, set_id, source_path) in db:
                        rows.writerow(dict(run_id=run_id, set_id=set_id,
                            source_path=source_path, url=data_url, path=local_path))
                    
                    print(local_path)
