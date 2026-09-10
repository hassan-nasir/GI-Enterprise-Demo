import json

result = env["bl.gi.enterprise.demo.service"].seed()
env.cr.commit()
print("GI_ENTERPRISE_SEED_RESULT")
print(json.dumps(result, indent=2, sort_keys=True, default=str))
