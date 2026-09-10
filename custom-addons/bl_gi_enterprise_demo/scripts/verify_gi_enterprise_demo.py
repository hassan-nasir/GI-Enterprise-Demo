import json

result = env["bl.gi.enterprise.demo.service"].verify()
print("GI_ENTERPRISE_VERIFY_RESULT")
print(json.dumps(result, indent=2, sort_keys=True, default=str))
