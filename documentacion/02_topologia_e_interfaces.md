# Topología y Mapeo de Interfaces - Sucursal 02
- R-SUC-02 (Cisco CSR1000v IOS XE 17.03.04a):
  * GigabitEthernet1: Enlace WAN a R-SUC-01 (10.255.0.2/30)
  * GigabitEthernet2: Enlace Troncal 802.1Q a SW-SUC-02-CORE
  * GigabitEthernet2.10: Gateway VLAN 10 (10.20.0.1/26)
  * GigabitEthernet2.20: Gateway VLAN 20 (10.20.0.65/27)
  * GigabitEthernet2.99: Gateway VLAN 99 (10.20.0.97/28)
- SW-SUC-02-CORE (Cisco IOSvL2):
  * GigabitEthernet0/0: Troncal dot1q a R-SUC-02
  * GigabitEthernet0/1: Acceso VLAN 10 (PC10)
  * GigabitEthernet0/2: Acceso VLAN 20 (PC9)
  * GigabitEthernet0/3: Acceso VLAN 99
