import json
with open('data/raw/wqmis/records.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        for r in data.get('results', []):
            if isinstance(r.get('value'), str):
                print(r)
                break
