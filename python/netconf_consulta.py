#!/usr/bin/env python3
"""
netconf_consulta.py
Fase 4: Consulta programática mediante NETCONF y procesamiento de modelos YANG.
"""

import sys
import xmltodict
from ncclient import manager

ROUTER_HOST = "10.255.0.2"
ROUTER_PORT = 830
ROUTER_USER = "netdevops"
ROUTER_PASS = "cisco123"

# Filtro NETCONF usando el modelo estándar ietf-interfaces
NETCONF_FILTER = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface/>
  </interfaces>
</filter>
"""

def main():
    print("=" * 75)
    print(" FASE 4: CONSULTA PROGRAMÁTICA NETCONF - R-SUC-02 (IOS XE)")
    print("=" * 75)
    print(f"[*] Conectando a {ROUTER_HOST}:{ROUTER_PORT} vía NETCONF/SSH...")

    try:
        with manager.connect(
            host=ROUTER_HOST,
            port=ROUTER_PORT,
            username=ROUTER_USER,
            password=ROUTER_PASS,
            hostkey_verify=False,
            device_params={'name': 'iosxe'},
            timeout=30
        ) as m:
            print("[✓] Sesión NETCONF establecida exitosamente.")
            print(f"[*] Session ID: {m.session_id}")
            print(f"[*] Número de capacidades anunciadas: {len(m.server_capabilities)}")

            # Realizar consulta get-config
            print("\n[*] Enviando rpc <get-config> con filtro ietf-interfaces...")
            response = m.get_config(source='running', filter=NETCONF_FILTER)
            xml_raw = response.xml

            # Guardar evidencia XML en evidencias/estado_inicial/
            archivo_evidencia = "evidencias/estado_inicial/netconf_interfaces_inicial.xml"
            with open(archivo_evidencia, "w", encoding="utf-8") as f:
                f.write(xml_raw)
            print(f"[✓] Evidencia XML original guardada en: {archivo_evidencia}")

            # Procesar XML a diccionario estructurado
            doc = xmltodict.parse(xml_raw)
            interfaces_data = doc.get('rpc-reply', {}).get('data', {}).get('interfaces', {}).get('interface', [])
            if isinstance(interfaces_data, dict):
                interfaces_data = [interfaces_data]

            print("\n" + "=" * 75)
            print(f"{'INTERFAZ':<22} {'ESTADO':<10} {'DIRECCIÓN IP':<18} {'MÁSCARA':<18}")
            print("=" * 75)

            for iface in interfaces_data:
                nombre = iface.get('name', 'N/A')
                enabled = "UP" if iface.get('enabled') == 'true' else "DOWN"
                
                # Extraer IP IPv4 si existe
                ipv4_info = iface.get('ietf-ip:ipv4', {}).get('address', {})
                if isinstance(ipv4_info, list) and len(ipv4_info) > 0:
                    ip_addr = ipv4_info[0].get('ip', 'Sin IP')
                    mask = ipv4_info[0].get('netmask', 'N/A')
                elif isinstance(ipv4_info, dict) and ipv4_info:
                    ip_addr = ipv4_info.get('ip', 'Sin IP')
                    mask = ipv4_info.get('netmask', 'N/A')
                else:
                    ip_addr = "Sin asignar"
                    mask = "-"

                print(f"{nombre:<22} {enabled:<10} {ip_addr:<18} {mask:<18}")

            print("=" * 75)
            print("[✓] Consulta y procesamiento NETCONF completados con éxito.\n")

    except Exception as e:
        print(f"[!] Error durante la sesión NETCONF: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
