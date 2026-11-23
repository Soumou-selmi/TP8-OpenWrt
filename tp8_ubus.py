import requests

URL = "http://192.168.1.1/ubus"
NULL_SESSION = "0" * 32


def call(obj, method, params=None, session=NULL_SESSION):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [session, obj, method, params or {}],
    }
    r = requests.post(URL, json=payload, timeout=5)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    code, *rest = data["result"]
    if code != 0:
        raise RuntimeError(f"ubus a renvoye le code {code}")
    return rest[0] if rest else {}


# Etape 2 : authentification
login = call("session", "login", {"username": "root", "password": "2004"})
sid = login["ubus_rpc_session"]
print("Session :", sid)
# Etape 3 : lecture de l'etat des interfaces
dump = call("network.interface", "dump", session=sid)

for itf in dump["interface"]:
    print("Interface :", itf["interface"], "| up :", itf["up"])
    for addr in itf.get("ipv4-address", []):
        print("   IPv4 :", addr["address"] + "/" + str(addr["mask"]))

# Statistiques de trafic du LAN
lan = next(i for i in dump["interface"] if i["interface"] == "lan")
print("Device LAN :", lan.get("device"))
print("IPv4 LAN :", lan["ipv4-address"])

# Etape 4 : modification via uci
print("IP avant :", call("uci", "get", {"config": "network", "section": "lan", "option": "ipaddr"}, session=sid))

call("uci", "set", {"config": "network", "section": "lan",
                    "values": {"ipaddr": "192.168.2.1"}}, session=sid)
call("uci", "commit", {"config": "network"}, session=sid)

print("IP apres :", call("uci", "get", {"config": "network", "section": "lan", "option": "ipaddr"}, session=sid))