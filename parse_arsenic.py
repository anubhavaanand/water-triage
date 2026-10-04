import json
with open('data/raw/wqmis/records.jsonl', 'r') as f:
    censored = {}
    for line in f:
        data = json.loads(line)
        if not data.get('test_results'): continue
        for r in data['test_results']:
            if 'Arsenic' in r.get('parameter_name', ''):
                val = r.get('test_result_value')
                if val and (val.strip().upper() == 'BDL' or '<' in val):
                    v = val.strip().upper()
                    censored[v] = censored.get(v, 0) + 1

    print("Censored counts:")
    for k, v in censored.items():
        print(f"{k}: {v}")
