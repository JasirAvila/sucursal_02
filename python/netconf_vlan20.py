#!/usr/bin/env python3
"""
netconf_vlan20.py
Fase 6: Configuración de la VLAN 20 (Operación) mediante NETCONF.
Aplica operaciones <edit-config> con modelos YANG nativos de IOS XE.
"""

import sys
import yaml
import xmltodict
from ncclient import manager

ROUTER_HOST = "10.255.0.2"
ROUTER_PORT = 830
ROUTER_USER = "netdevops"
ROUTER_PASS = "cisco123"

def main():
    print("=" * 75)
    print(" FASE 6: CONFIGURACIÓN MEDIANTE NETCONF - VLAN 20 (OPERACION)")
    print("=" * 75)

    # 1. Cargar datos desde YAML
    with open("datos/sucursal_02_generada.yml", "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    vlan20 = next((v for v in data_yaml['sucursal_02']['vlans'] if v['id'] == 20), None)
    if not vlan20:
        print("[!] Error: No se encontró la VLAN 20 en datos/sucursal_02_generada.yml")
        sys.exit(1)

    subif_name = "2.20"
    vlan_id = vlan20['id']
    desc = f"VLAN {vlan_id} - {vlan20['nombre']}"
    ip_addr = vlan20['gateway']
    mask = vlan20['mascara']

    print(f"[*] Parámetros leídos de datos/sucursal_02_generada.yml:")
    print(f"    Subinterfaz: GigabitEthernet{subif_name}")
    print(f"    VLAN ID:     {vlan_id}")
    print(f"    Descripción: {desc}")
    print(f"    IP Gateway:  {ip_addr}")
    print(f"    Máscara:     {mask}")

    # Filtro de consulta para la subinterfaz 2.20
    filter_vlan20 = f"""
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

    # Payload XML para <edit-config>
    xml_payload = f"""
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
          <GigabitEthernet>
            <name>{subif_name}</name>
            <description>{desc}</description>
            <encapsulation>
              <dot1Q>
                <vlan-id>{vlan_id}</vlan-id>
              </dot1Q>
            </encapsulation>
            <ip>
              <address>
                <primary>
                  <address>{ip_addr}</address>
                  <mask>{mask}</mask>
                </primary>
              </address>
            </ip>
          </GigabitEthernet>
        </interface>
      </native>
    </config>
    """

    try:
        print(f"\n[*] Conectando a {ROUTER_HOST}:{ROUTER_PORT} vía NETCONF/SSH...")
        with manager.connect(
            host=ROUTER_HOST,
            port=ROUTER_PORT,
            username=ROUTER_USER,
            password=ROUTER_PASS,
            hostkey_verify=False,
            device_params={'name': 'iosxe'},
            timeout=30
        ) as m:
            print("[✓] Sesión NETCONF establecida.")

            # 2. Comprobar estado anterior
            print("\n[*] 1. Consultando estado previo vía <get-config>...")
            res_antes = m.get_config(source='running', filter=filter_vlan20)
            xml_antes = res_antes.xml

            archivo_antes = "evidencias/estado_inicial/netconf_vlan20_antes.xml"
            with open(archivo_antes, "w", encoding="utf-8") as f:
                f.write(xml_antes)
            print(f"    [✓] Evidencia de estado previo guardada en: {archivo_antes}")

            # 3. Aplicar configuración con <edit-config>
            print("\n[*] 2. Carga útil XML a enviar (<edit-config>):")
            print(xml_payload.strip())

            print("\n[*] 3. Enviando rpc <edit-config> al datastore 'running'...")
            edit_reply = m.edit_config(target='running', config=xml_payload)
            print(f"    [✓] Respuesta del router a edit-config: {edit_reply.xml}")

            # 4. Comprobación del estado resultante
            print("\n[*] 4. Verificando estado resultante vía <get-config>...")
            res_despues = m.get_config(source='running', filter=filter_vlan20)
            xml_despues = res_despues.xml

            archivo_despues = "evidencias/estado_final/netconf_vlan20_despues.xml"
            with open(archivo_despues, "w", encoding="utf-8") as f:
                f.write(xml_despues)
            print(f"    [✓] Evidencia de estado final guardada en: {archivo_despues}")

            # Procesar y validar respuesta
            doc = xmltodict.parse(xml_despues)
            subif_data = doc.get('rpc-reply', {}).get('data', {}).get('native', {}).get('interface', {}).get('GigabitEthernet', {})

            if subif_data and subif_data.get('name') == subif_name:
                vlan_encap = subif_data.get('encapsulation', {}).get('dot1Q', {}).get('vlan-id')
                ip_cfg = subif_data.get('ip', {}).get('address', {}).get('primary', {}).get('address')
                mask_cfg = subif_data.get('ip', {}).get('address', {}).get('primary', {}).get('mask')

                print("\n" + "=" * 75)
                print(" CONFIGURACIÓN VERIFICADA MEDIANTE MODELO YANG (NETCONF):")
                print(f"  * Subinterfaz:   GigabitEthernet{subif_data.get('name')}")
                print(f"  * Descripción:   {subif_data.get('description')}")
                print(f"  * VLAN dot1Q:    {vlan_encap}")
                print(f"  * IP Gateway:    {ip_cfg}")
                print(f"  * Máscara:       {mask_cfg}")
                print("=" * 75)
                print(f"[✓] FASE 6 COMPLETADA: VLAN 20 ({ip_cfg}/{mask_cfg}) operativa por NETCONF.\n")
            else:
                print("[!] Advertencia: No se encontraron los datos esperados en la respuesta XML.")

    except Exception as e:
        print(f"[!] Error durante la sesión NETCONF: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
