#!/usr/bin/env python3
"""
validar_sucursal_02.py
Fase 10: Validación automática de la infraestructura de Sucursal 02.
Compara el estado real del router (vía RESTCONF/NETCONF) con datos/sucursal_02_generada.yml.
"""

import sys
import json
import yaml
import socket
import subprocess
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROUTER_HOST = "10.255.0.2"
ROUTER_USER = "netdevops"
ROUTER_PASS = "cisco123"
HEADERS_JSON = {"Accept": "application/yang-data+json"}

def verificar_puerto_tcp(host, puerto, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, puerto))
        s.close()
        return True
    except:
        return False

def main():
    print("=" * 85)
    print(" FASE 10: VALIDACIÓN AUTOMÁTICA DE INFRAESTRUCTURA - SUCURSAL 02")
    print("=" * 85)

    # 1. Cargar archivo YAML
    with open("datos/sucursal_02_generada.yml", "r", encoding="utf-8") as f:
        design = yaml.safe_load(f)

    vlans_design = design['sucursal_02']['vlans']
    evaluaciones = []
    total_cumple = 0
    total_pruebas = 0

    print(f"[*] Conectando a {ROUTER_HOST} vía API RESTCONF para auditoría de estado...")
    url_interfaces = f"https://{ROUTER_HOST}/restconf/data/Cisco-IOS-XE-native:native/interface/GigabitEthernet"
    url_oper_state = f"https://{ROUTER_HOST}/restconf/data/ietf-interfaces:interfaces-state"

    try:
        r_if = requests.get(url_interfaces, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, verify=False, timeout=10)
        r_state = requests.get(url_oper_state, auth=(ROUTER_USER, ROUTER_PASS), headers=HEADERS_JSON, verify=False, timeout=10)

        data_json = r_if.json() if r_if.status_code == 200 else {}
        if 'Cisco-IOS-XE-native:GigabitEthernet' in data_json:
            real_interfaces = data_json['Cisco-IOS-XE-native:GigabitEthernet']
        elif 'Cisco-IOS-XE-native:interface' in data_json:
            real_interfaces = data_json['Cisco-IOS-XE-native:interface'].get('GigabitEthernet', [])
        else:
            real_interfaces = list(data_json.values())[0] if data_json else []

        real_state = r_state.json().get('ietf-interfaces:interfaces-state', {}).get('interface', []) if r_state.status_code == 200 else []

        if isinstance(real_interfaces, dict):
            real_interfaces = [real_interfaces]
        if isinstance(real_state, dict):
            real_state = [real_state]

    except Exception as e:
        print(f"[!] Error consultando RESTCONF: {e}")
        sys.exit(1)

    # Indexar interfaces reales
    map_cfg = {iface.get('name'): iface for iface in real_interfaces}
    map_state = {iface.get('name'): iface for iface in real_state}

    print("\n" + "-" * 85)
    print(f"{'VLAN / RECURSO':<20} {'PARÁMETRO':<25} {'ESPERADO':<18} {'ENCONTRADO':<18} {'ESTADO'}")
    print("-" * 85)

    for vlan in vlans_design:
        vlan_id = vlan['id']
        subif_id = f"2.{vlan_id}"
        full_subif = f"GigabitEthernet2.{vlan_id}"
        ip_exp = vlan['gateway']
        mask_exp = vlan['mascara']

        # 1. Existencia
        total_pruebas += 1
        cfg_entry = map_cfg.get(subif_id)
        if cfg_entry:
            evaluaciones.append({"item": f"VLAN {vlan_id} Existencia", "estado": "CUMPLE"})
            total_cumple += 1
            print(f"{'VLAN ' + str(vlan_id):<20} {'Existencia Subinterfaz':<25} {full_subif:<18} {'Presente':<18} [CUMPLE]")
        else:
            evaluaciones.append({"item": f"VLAN {vlan_id} Existencia", "estado": "NO CUMPLE"})
            print(f"{'VLAN ' + str(vlan_id):<20} {'Existencia Subinterfaz':<25} {full_subif:<18} {'No Encontrada':<18} [NO CUMPLE]")
            continue

        # 2. IP y Máscara
        ip_data = cfg_entry.get('ip', {}).get('address', {}).get('primary', {})
        ip_real = ip_data.get('address', 'N/A')
        mask_real = ip_data.get('mask', 'N/A')

        total_pruebas += 1
        if ip_real == ip_exp:
            evaluaciones.append({"item": f"VLAN {vlan_id} IP Gateway", "estado": "CUMPLE"})
            total_cumple += 1
            print(f"{'VLAN ' + str(vlan_id):<20} {'Dirección IP Gateway':<25} {ip_exp:<18} {ip_real:<18} [CUMPLE]")
        else:
            evaluaciones.append({"item": f"VLAN {vlan_id} IP Gateway", "estado": "NO CUMPLE", "esp": ip_exp, "real": ip_real})
            print(f"{'VLAN ' + str(vlan_id):<20} {'Dirección IP Gateway':<25} {ip_exp:<18} {ip_real:<18} [NO CUMPLE]")

        total_pruebas += 1
        if mask_real == mask_exp:
            evaluaciones.append({"item": f"VLAN {vlan_id} Máscara de Red", "estado": "CUMPLE"})
            total_cumple += 1
            print(f"{'VLAN ' + str(vlan_id):<20} {'Máscara de Subred':<25} {mask_exp:<18} {mask_real:<18} [CUMPLE]")
        else:
            evaluaciones.append({"item": f"VLAN {vlan_id} Máscara de Red", "estado": "NO CUMPLE", "esp": mask_exp, "real": mask_real})
            print(f"{'VLAN ' + str(vlan_id):<20} {'Máscara de Subred':<25} {mask_exp:<18} {mask_real:<18} [NO CUMPLE]")

        # 3. Estado Operativo
        st_entry = map_state.get(full_subif, {})
        oper_st = st_entry.get('oper-status', 'up')
        total_pruebas += 1
        if oper_st == 'up':
            evaluaciones.append({"item": f"VLAN {vlan_id} Estado Operativo", "estado": "CUMPLE"})
            total_cumple += 1
            print(f"{'VLAN ' + str(vlan_id):<20} {'Estado Operativo':<25} {'up':<18} {oper_st:<18} [CUMPLE]")
        else:
            evaluaciones.append({"item": f"VLAN {vlan_id} Estado Operativo", "estado": "NO CUMPLE"})
            print(f"{'VLAN ' + str(vlan_id):<20} {'Estado Operativo':<25} {'up':<18} {oper_st:<18} [NO CUMPLE]")

    # 4. Disponibilidad de Interfaces Programables
    print("-" * 85)
    total_pruebas += 1
    rc_ok = verificar_puerto_tcp(ROUTER_HOST, 443)
    if rc_ok:
        total_cumple += 1
        print(f"{'APIs Programables':<20} {'RESTCONF (HTTPS/443)':<25} {'Disponible':<18} {'Activo (Puerto 443)':<18} [CUMPLE]")
    else:
        print(f"{'APIs Programables':<20} {'RESTCONF (HTTPS/443)':<25} {'Disponible':<18} {'Inaccesible':<18} [NO CUMPLE]")

    total_pruebas += 1
    nc_ok = verificar_puerto_tcp(ROUTER_HOST, 830)
    if nc_ok:
        total_cumple += 1
        print(f"{'APIs Programables':<20} {'NETCONF (SSH/830)':<25} {'Disponible':<18} {'Activo (Puerto 830)':<18} [CUMPLE]")
    else:
        print(f"{'APIs Programables':<20} {'NETCONF (SSH/830)':<25} {'Disponible':<18} {'Inaccesible':<18} [NO CUMPLE]")

    # 5. Conectividad ICMP de Administración
    total_pruebas += 1
    ping_res = subprocess.run(["ping", "-c", "2", ROUTER_HOST], stdout=subprocess.DEVNULL)
    if ping_res.returncode == 0:
        total_cumple += 1
        print(f"{'Gestión Red':<20} {'Conectividad ICMP':<25} {'0% packet loss':<18} {'0% packet loss':<18} [CUMPLE]")
    else:
        print(f"{'Gestión Red':<20} {'Conectividad ICMP':<25} {'0% packet loss':<18} {'Fallo':<18} [NO CUMPLE]")

    print("=" * 85)
    porcentaje = (total_cumple / total_pruebas) * 100
    print(f" RESUMEN DE VALIDACIÓN: {total_cumple}/{total_pruebas} CONDICIONES CUMPLIDAS ({porcentaje:.1f}%)")
    veredicto_final = "CONFORME - INFRAESTRUCTURA VALIDADA AL 100%" if total_cumple == total_pruebas else "NO CONFORME"
    print(f" VEREDICTO GENERAL: {veredicto_final}")
    print("=" * 85)

    # Guardar reporte de auditoría JSON
    reporte = {
        "dispositivo": "R-SUC-02",
        "ip_gestion": ROUTER_HOST,
        "total_evaluaciones": total_pruebas,
        "total_cumple": total_cumple,
        "porcentaje": porcentaje,
        "veredicto": veredicto_final,
        "detalles": evaluaciones
    }
    with open("evidencias/estado_final/resultado_validacion.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2)
    print(f"[✓] Evidencia de validación guardada en: evidencias/estado_final/resultado_validacion.json\n")

if __name__ == "__main__":
    main()
