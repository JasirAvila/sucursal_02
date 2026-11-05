# Proyecto NetDevOps: Implementación Sucursal 02 (APIs y Programabilidad)

## Infraestructura y Dispositivos
- **Router:** Cisco CSR1000v (IOS XE 17.03.04a) - R-SUC-02
- **Switch:** Cisco IOSvL2 - SW-SUC-02-CORE
- **Servidor:** Ubuntu 26.04 LTS (NETDEVOPS-SRV)

## Estructura del Repositorio
- `python/`: Scripts de consulta, configuración y auditoría (NETCONF, RESTCONF, Validador).
- `datos/`: Archivo de diseño `sucursal_02_generada.yml`.
- `evidencias/estado_inicial/`: XMLs y JSONs de estado previo.
- `evidencias/estado_final/`: XMLs, JSONs y resultados de auditoría 15/15.
- `documentacion/`: Especificaciones técnicas y memorias de cálculo.

## Ejecución de Programas
```bash
# Fase 4: Consulta NETCONF
python3 python/netconf_consulta.py

# Fase 5: Configuración RESTCONF VLAN 10
python3 python/restconf_vlan10.py

# Fase 6: Configuración NETCONF VLAN 20
python3 python/netconf_vlan20.py

# Fase 7: Interoperabilidad VLAN 99
python3 python/interoperabilidad_vlan99.py

# Fase 10: Validación Automática
python3 python/validar_sucursal_02.py

