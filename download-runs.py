import requests, io, csv, hashlib, time, os
from urllib.parse import urlparse

states = '''
https://results.openaddresses.io/sets/-63331/state.txt
https://results.openaddresses.io/sets/-54733/state.txt
https://results.openaddresses.io/sets/-44438/state.txt
https://results.openaddresses.io/sets/-36544/state.txt
https://results.openaddresses.io/sets/-27542/state.txt
https://results.openaddresses.io/sets/-20088/state.txt
https://results.openaddresses.io/sets/-13308/state.txt
https://results.openaddresses.io/sets/-1963/state.txt
https://results.openaddresses.io/sets/18859/state.txt
https://results.openaddresses.io/sets/24465/state.txt
https://results.openaddresses.io/sets/30562/state.txt
https://results.openaddresses.io/sets/43050/state.txt

https://results.openaddresses.io/sets/52181/state.txt
https://results.openaddresses.io/sets/58315/state.txt
https://results.openaddresses.io/sets/65703/state.txt
https://results.openaddresses.io/sets/73276/state.txt
https://results.openaddresses.io/sets/80311/state.txt
https://results.openaddresses.io/sets/85697/state.txt
https://results.openaddresses.io/sets/92640/state.txt
https://results.openaddresses.io/sets/100816/state.txt
https://results.openaddresses.io/sets/108487/state.txt
https://results.openaddresses.io/sets/115738/state.txt
https://results.openaddresses.io/sets/123450/state.txt
https://results.openaddresses.io/sets/131277/state.txt

https://results.openaddresses.io/sets/141476/state.txt
'''

seen_urls = {''}

for url in states.split():
    print('Getting', url)
    got = requests.get(url)
    states = csv.DictReader(io.StringIO(got.text), dialect='excel-tab')
    for state in states:
        source_path, processed_url = state['source'], state['processed']

        if source_path[:6] not in ('us-ca-', 'us/ca/'):
            continue
        elif processed_url in seen_urls:
            continue
        else:
            seen_urls.add(processed_url)

        processed_url_hash = hashlib.sha1(processed_url.encode('utf8'))
        _, processed_url_ext = os.path.splitext(urlparse(processed_url).path)
        source_path_base, _ = os.path.splitext(source_path)
        processed_dirname = os.path.join('downloaded', processed_url_hash.hexdigest()[:12])
        processed_filename = os.path.join(processed_dirname, source_path_base + processed_url_ext)
        print(source_path, processed_url, '->', processed_filename)
        
        os.makedirs(os.path.dirname(processed_filename))

        with open(os.path.join(processed_dirname, 'URL.txt'), 'w') as file:
            print(processed_url, file=file)
            print(os.path.relpath(processed_filename, processed_dirname), file=file)
        with open(processed_filename, 'wb') as file:
            print('Getting', processed_url)
            got = requests.get(processed_url)
            file.write(got.content)
        
        time.sleep(1)
