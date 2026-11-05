#!/usr/bin/env python3
"""
restconf_vlan10.py
Fase 5: Configuración de la VLAN 10 (Administración) mediante RESTCONF.
Lee los parámetros desde datos/sucursal_02_generada.yml.
"""

import sys
import json
import yaml
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROUTER_HOST = "10.255.0.2"
ROUTER_USER = "netdevops"
ROUTER_PASS = "cisco123"
HEADERS_JSON = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
BASE_URL = f"https://{ROUTER_HOST}/restconf/data/Cisco-IOS-XE-native:native/interface"

def main():
    print("=" * 75)
    print(" FASE 5: CONFIGURACIÓN MEDIANTE RESTCONF - VLAN 10 (ADMINISTRACION)")
    print("=" * 75)

    # 1. Cargar datos desde YAML
    with open("datos/sucursal_02_generada.yml", "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    vlan10 = next((v for v in data_yaml['sucursal_02']['vlans'] if v['id'] == 10), None)
    if not vlan10:
        print("[!] Error: No se encontró la VLAN 10 en datos/sucursal_02_generada.yml")
        sys.exit(1)

    subif_name = "2.10"
    vlan_id = vlan10['id']
    desc = f"VLAN {vlan_id} - {vlan10['nombre']}"
    ip_addr = vlan10['gateway']
    mask = vlan10['mascara']

    print(f"[*] Parámetros leídos de datos/sucursal_02_generada.yml:")
    print(f"    Subinterfaz: GigabitEthernet{subif_name}")
    print(f"    VLAN ID:     {vlan_id}")
    print(f"    Descripción: {desc}")
    print(f"    IP Gateway:  {ip_addr}")
    print(f"    Máscara:     {mask}")

    # 2. Comprobación del estado anterior (GET)
    target_url = f"{BASE_URL}/GigabitEthernet={subif_name}"
    print(f"\n[*] 1. Consultando estado previo vía GET: {target_url}...")
    resp_antes = requests.get(target_url, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, verify=False)
    print(f"    Código HTTP previo: {resp_antes.status_code} ({'No existe aún (esperado)' if resp_antes.status_code == 404 else 'Ya existe'})")

    with open("evidencias/estado_inicial/restconf_vlan10_antes.json", "w", encoding="utf-8") as f:
        f.write(resp_antes.text if resp_antes.text else json.dumps({"status": resp_antes.status_code, "msg": "Subinterface does not exist"}))
    print("    [✓] Evidencia de estado inicial guardada.")

    # 3. Construir carga útil JSON
    payload = {
        "Cisco-IOS-XE-native:interface": {
            "GigabitEthernet": [
                {
                    "name": subif_name,
                    "description": desc,
                    "encapsulation": {
                        "dot1Q": {
                            "vlan-id": vlan_id
                        }
                    },
                    "ip": {
                        "address": {
                            "primary": {
                                "address": ip_addr,
                                "mask": mask
                            }
                        }
                    }
                }
            ]
        }
    }

    print("\n[*] 2. Carga útil JSON construida:")
    print(json.dumps(payload, indent=2))

    # 4. Enviar cambio mediante PATCH
    print(f"\n[*] 3. Enviando configuración vía PATCH a {BASE_URL}...")
    resp_patch = requests.patch(BASE_URL, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, json=payload, verify=False)
    print(f"    Código HTTP de respuesta: {resp_patch.status_code}")

    if resp_patch.status_code not in [200, 201, 204]:
        print(f"[!] Error aplicando PATCH: {resp_patch.text}")
        sys.exit(1)
    print("    [✓] Petición PATCH aceptada por el router.")

    # 5. Comprobación del estado resultante (GET)
    print(f"\n[*] 4. Verificando estado resultante vía GET: {target_url}...")
    resp_despues = requests.get(target_url, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, verify=False)
    print(f"    Código HTTP posterior: {resp_despues.status_code}")

    if resp_despues.status_code == 200:
        print("    [✓] ¡Subinterfaz verificada exitosamente en el router!")
        print("\n[*] Configuración resultante en formato JSON:")
        print(json.dumps(resp_despues.json(), indent=2))

        with open("evidencias/estado_final/restconf_vlan10_despues.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(resp_despues.json(), indent=2))
        print(f"\n[✓] Evidencia guardada en: evidencias/estado_final/restconf_vlan10_despues.json")
    else:
        print(f"[!] Error verificando configuración: {resp_despues.text}")
        sys.exit(1)

    print("=" * 75)
    print(f"[✓] FASE 5 COMPLETADA: VLAN 10 ({ip_addr}/{mask}) operativa por RESTCONF.\n")

if __name__ == "__main__":
    main()
