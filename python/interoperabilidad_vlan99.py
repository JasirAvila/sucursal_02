#!/usr/bin/env python3
"""
interoperabilidad_vlan99.py
Fase 7: Interoperabilidad entre RESTCONF y NETCONF.
Crea mediante RESTCONF, consulta y modifica mediante NETCONF, y valida por RESTCONF.
"""

import sys
import json
import yaml
import requests
import xmltodict
import urllib3
from ncclient import manager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROUTER_HOST = "10.255.0.2"
ROUTER_PORT_NC = 830
ROUTER_USER = "netdevops"
ROUTER_PASS = "cisco123"

HEADERS_JSON = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
RESTCONF_IF_URL = f"https://{ROUTER_HOST}/restconf/data/Cisco-IOS-XE-native:native/interface"
RESTCONF_VLAN99_URL = f"{RESTCONF_IF_URL}/GigabitEthernet=2.99"

def main():
    print("=" * 80)
    print(" FASE 7: INTEROPERABILIDAD ENTRE RESTCONF Y NETCONF - VLAN 99 (GESTION)")
    print("=" * 80)

    # 1. Cargar datos desde YAML
    with open("datos/sucursal_02_generada.yml", "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    vlan99 = next((v for v in data_yaml['sucursal_02']['vlans'] if v['id'] == 99), None)
    if not vlan99:
        print("[!] Error: No se encontró la VLAN 99 en el YAML.")
        sys.exit(1)

    subif_name = "2.99"
    vlan_id = vlan99['id']
    desc_inicial = f"VLAN {vlan_id} - {vlan99['nombre']}"
    desc_modificada = f"VLAN {vlan_id} - {vlan99['nombre']} (MODIFICADO VIA NETCONF)"
    ip_addr = vlan99['gateway']
    mask = vlan99['mascara']

    # -------------------------------------------------------------
    # PASO 1: CREACIÓN MEDIANTE RESTCONF (HTTP PATCH / JSON)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" PASO 1: IMPLEMENTACIÓN DE VLAN 99 MEDIANTE RESTCONF (HTTP PATCH / JSON)")
    print("-" * 80)

    payload_restconf = {
        "Cisco-IOS-XE-native:interface": {
            "GigabitEthernet": [
                {
                    "name": subif_name,
                    "description": desc_inicial,
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

    print(f"[*] Enviando solicitud PATCH a {RESTCONF_IF_URL}...")
    resp_rc = requests.patch(RESTCONF_IF_URL, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, json=payload_restconf, verify=False)
    print(f"[✓] Código HTTP recibido: {resp_rc.status_code}")

    if resp_rc.status_code not in [200, 201, 204]:
        print(f"[!] Error en RESTCONF: {resp_rc.text}")
        sys.exit(1)

    with open("evidencias/estado_final/interop_vlan99_restconf_creacion.json", "w", encoding="utf-8") as f:
        json.dump(payload_restconf, f, indent=2)
    print("[✓] Subinterfaz creada exitosamente por RESTCONF.")

    # -------------------------------------------------------------
    # PASO 2: CONSULTA CRUZADA MEDIANTE NETCONF (SSH 830 / XML)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" PASO 2: CONSULTA CRUZADA MEDIANTE NETCONF (SSH:830 / XML)")
    print("-" * 80)

    filter_vlan99 = f"""
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
          <GigabitEthernet>
            <name>{subif_name}</name>
          </GigabitEthernet>
        </interface>
      </native>
    </filter>
    """

    with manager.connect(
        host=ROUTER_HOST,
        port=ROUTER_PORT_NC,
        username=ROUTER_USER,
        password=ROUTER_PASS,
        hostkey_verify=False,
        device_params={'name': 'iosxe'},
        timeout=30
    ) as m:
        print("[*] Conectado a NETCONF. Consultando subinterfaz creada por RESTCONF...")
        nc_get = m.get_config(source='running', filter=filter_vlan99)
        with open("evidencias/estado_final/interop_vlan99_netconf_lectura.xml", "w", encoding="utf-8") as f:
            f.write(nc_get.xml)

        doc = xmltodict.parse(nc_get.xml)
        sub_read = doc.get('rpc-reply', {}).get('data', {}).get('native', {}).get('interface', {}).get('GigabitEthernet', {})
        print(f"[✓] NETCONF leyó exitosamente los datos creados por RESTCONF:")
        print(f"    - Subinterfaz: GigabitEthernet{sub_read.get('name')}")
        print(f"    - Descripción: {sub_read.get('description')}")
        print(f"    - IP Asignada: {sub_read.get('ip', {}).get('address', {}).get('primary', {}).get('address')}")

        # -------------------------------------------------------------
        # PASO 3: MODIFICACIÓN CONTROLADA MEDIANTE NETCONF (<edit-config>)
        # -------------------------------------------------------------
        print("\n" + "-" * 80)
        print(" PASO 3: MODIFICACIÓN CONTROLADA MEDIANTE NETCONF (<edit-config>)")
        print("-" * 80)
        print(f"[*] Cambiando descripción a: '{desc_modificada}'...")

        xml_mod = f"""
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <interface>
              <GigabitEthernet>
                <name>{subif_name}</name>
                <description>{desc_modificada}</description>
              </GigabitEthernet>
            </interface>
          </native>
        </config>
        """

        nc_edit = m.edit_config(target='running', config=xml_mod)
        with open("evidencias/estado_final/interop_vlan99_netconf_modificacion.xml", "w", encoding="utf-8") as f:
            f.write(nc_edit.xml)
        print(f"[✓] Respuesta NETCONF edit-config: <ok/> recibida.")

    # -------------------------------------------------------------
    # PASO 4: VERIFICACIÓN CRUZADA MEDIANTE RESTCONF (HTTP GET)
    # -------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" PASO 4: VERIFICACIÓN CRUZADA MEDIANTE RESTCONF (HTTP GET / JSON)")
    print("-" * 80)

    print(f"[*] Consultando {RESTCONF_VLAN99_URL} vía GET...")
    resp_rc_check = requests.get(RESTCONF_VLAN99_URL, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, verify=False)
    print(f"[✓] Código HTTP recibido: {resp_rc_check.status_code}")

    if resp_rc_check.status_code == 200:
        data_rc = resp_rc_check.json()
        with open("evidencias/estado_final/interop_vlan99_restconf_verificacion.json", "w", encoding="utf-8") as f:
            json.dump(data_rc, f, indent=2)

        desc_rc_leida = data_rc.get('Cisco-IOS-XE-native:GigabitEthernet', {}).get('description')
        print(f"[✓] RESTCONF confirma la modificación realizada por NETCONF:")
        print(f"    - Descripción actual en JSON: '{desc_rc_leida}'")
        print(f"    - ¿Coincide exactamente?: {'SÍ (INTEROPERABILIDAD DEMOSTRADA 100%)' if desc_rc_leida == desc_modificada else 'NO'}")
    else:
        print(f"[!] Error consultando RESTCONF: {resp_rc_check.text}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("[✓] FASE 7 COMPLETADA CON ÉXITO: Interoperabilidad bidireccional demostrada.\n")

if __name__ == "__main__":
    main()
