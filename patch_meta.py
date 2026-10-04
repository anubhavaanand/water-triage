import re

with open('backend/app/api/meta.py', 'r') as f:
    content = f.read()

# Add critical_concentration query before return
query = """
    # Critical concentration logic
    crit_conc = db.execute(text('''
        SELECT d.name as district, COUNT(ws.id) as total_critical,
               SUM(CASE WHEN 
                     (SELECT COUNT(*) FROM readings WHERE sample_id = ws.id) = 1 
                     AND 
                     (SELECT parameter_key FROM readings WHERE sample_id = ws.id LIMIT 1) = 'iron'
                   THEN 1 ELSE 0 END) as single_param_iron_critical
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        WHERE rs.score >= 75
        GROUP BY d.name
        ORDER BY total_critical DESC
        LIMIT 1;
    ''')).fetchone()
    
    critical_concentration = None
    if crit_conc:
        critical_concentration = {
            "district": crit_conc[0],
            "total_critical": int(crit_conc[1]),
            "single_parameter_iron_critical": int(crit_conc[2]),
        }

    return {
"""
content = content.replace("    return {", query)

# Add critical_concentration to return dict
content = content.replace('"bands": bands_dict,', '"bands": bands_dict,\n        "critical_concentration": critical_concentration,')

# Replace the has_permissible block manually:
content = content.replace("MAX(CASE WHEN bp.permissible_limit IS NULL THEN 1 ELSE 0 END) as no_permissible", "MAX(CASE WHEN bp.permissible_limit IS NULL OR bp.permissible_limit <= bp.acceptable_limit THEN 1 ELSE 0 END) as no_permissible")

# Replace python derivation
old_code = """
        prates = []
        no_relax = ["iron", "nitrate", "ph", "e_coli"]
        for pr in param_rates:
            key = pr[0]
            is_no_relax = key in no_relax
            prates.append({
                "parameter_key": key,
                "tested": pr[1],
                "exceeding_acceptable": pr[2],
                "exceeding_permissible": None if is_no_relax else pr[3],
                "has_permissible": not is_no_relax
            })"""
new_code = """
        prates = []
        for pr in param_rates:
            key = pr[0]
            is_no_relax = pr[4] == 1
            prates.append({
                "parameter_key": key,
                "tested": pr[1],
                "exceeding_acceptable": pr[2],
                "exceeding_permissible": None if is_no_relax else pr[3],
                "has_permissible": not is_no_relax
            })"""
content = content.replace(old_code, new_code)

with open('backend/app/api/meta.py', 'w') as f:
    f.write(content)
