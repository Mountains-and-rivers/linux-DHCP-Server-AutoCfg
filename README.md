# linux-DHCP-Server-AutoCfg
自动化实现对linux服务器的控制，对于tcl语言来说需要封装ssh通道，而Python自带的paramiko拓展包就可实现。
使用范围：网络服务器配置，网络设备测试，运维等。
使用SSH对远程Linux服务器进行配置，主要分2步:
1、服务器配置参数。
2、服务器启动。
SSH发送pidof dhcpd 命令可以获取进程号查看进程是否起来。 
其他服务器（PPPOE、L2TP、PPTP、DNS）实现逻辑类似，也可实现对远程Linux下的程序启动/信息获取等，DHCP进作为一个实现思路参考。
