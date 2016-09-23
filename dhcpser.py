# -*- coding: utf-8 -*-   
from PyQt4.QtGui import *  
from PyQt4.QtCore import * 
from Form_DhcpSer import Ui_DhcpSer
from PyQt4 import QtGui,QtCore, uic
from global_net import *
import sys,re,paramiko,threading,os,time,getopt,array
if __name__ != "__main__":
    from global_net import *
QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))  
from configobj import ConfigObj
class DhcpSer(QtGui.QWidget):  
    """初始化函数加载参数"""
    def __init__(self,parent=None):  
        super(DhcpSer,self).__init__(parent)
        self.ui=Ui_DhcpSer()        
        self.ui.setupUi(self)
        self.parent=parent
        self.load_para()
        self.dhcpstatus="stop"
        self.ui.save.clicked.connect(self.dhcpser_config)
        self.ui.lnk_ip.currentIndexChanged.connect(self.change_para)  
        #self.ui.pushButton_test.clicked.connect(self.test_start)
        #layout=QGridLayout()  
        #self.setLayout(layout)  
    def dhcpser_config(self):
        qtm=QtGui.QMessageBox
        self.get_para()
        if self.dhcpstatus == "running":
            self.dhcpstatus = "stop"
            stdin,stdout,stderr=conn_ssh['serv'].exec_command("pidof dhcpd",timeout=20.0)
            dhcp_pid = stdout.read()
            if dhcp_pid:
                stdin,stdout,stderr=conn_ssh['serv'].exec_command("kill -9 %s;rm -rf /tmp/dhcpd.conf" %(dhcp_pid),timeout=20.0)
            self.ui.serstatus.setText(u"服务器已关闭")
            self.ui.save.setText(u"开启服务器")
            return True
        # print stdout.read()
        #1、获取地址后设置接口Ip地址
        #2、配置服务器DHCP服务器参数
        #3、开启服务器并保存信息
        #
        cmdstr='killall -9 dhcpd\n'
        if self.if_name and self.if_ip and self.if_mask:
            cmdstr = cmdstr+"ifconfig %s %s netmask %s up\n" %(self.if_name,self.if_ip,self.if_mask)
        else:
            msg_box = qtm(qtm.Warning, "Alert", u"接口,Ip地址和子网掩码不能为空")
            msg_box.exec_()
            return
        #2、根据参数生成配置文件
        #
        leasestr=""
        lease_flag="-addop 51,4,N4:-1."
        print "self.lease_time=",self.lease_time
        if self.lease_time != "-1":
            leasestr="--lease %s" %(self.lease_time)
            print "leasestr=",leasestr
            lease_flag=""
        cmdstr=cmdstr+"/var/tendatest/TDT/script/config_DhcpSerCfg.sh -o /tmp/dhcpd.conf %s --iprange %s,%s --dns %s --routers %s --netmask %s\n" %(leasestr,self.start_ip,self.end_ip,self.dns_ip,self.gateway_ip,self.if_mask)
        print "cmdstr=",cmdstr
        if len(self.opt33_dst.split(".")) == 4:
            opt33_args="-addop 33,8,I:%s,%s." %(self.opt33_dst,self.opt33_next_hop)
        elif self.opt33_dst.split(".") != "" and len(self.opt33_dst.split(".")) != 4:
            msg_box = qtm(qtm.Warning, "Alert", u"option 33目的地址不合法")
            msg_box.exec_()
            return
        else:
            opt33_args=""
        if self.opt121_net:
            netlen = (int(self.opt121_net)-1)/8
            dstlen=netlen+1
            iplst=self.opt121_dst.split(".")
            # ipnet=""
            # for i in range(0,dstlen):
                # ipnet=ipnet+iplst[:dstlen][i]+"."
            # ipnet=ipnet+self.opt121_next_hop
            ipnet=".".join(iplst[:dstlen])+"."+self.opt121_next_hop
            ipnet=ipnet.replace(".",",")
            print "ipnet=",ipnet
            opt121_args="-addop 121,%d,N1:%s,%s." %(netlen+6,self.opt121_net,ipnet)
        else:
            opt121_args=""     
        if self.opt249_net:
            netlen = (int(self.opt249_net)-1)/8
            dstlen=netlen+1
            iplst=self.opt249_dst.split(".")
            # ipnet=""
            # for i in range(0,dstlen):
                # ipnet=ipnet+iplst[:dstlen][i]+"."
            # ipnet=ipnet+self.opt249_next_hop
            ipnet=".".join(iplst[:dstlen])+"."+self.opt249_next_hop
            ipnet=ipnet.replace(".",",")
            print "ipnet249=",ipnet
            opt249_args="-addop 249,%d,N1:%s,%s." %(netlen+6,self.opt121_net,ipnet)
        else:
            opt249_args=""
        ackstr=""
        if self.ack_checkbox:
            ackstr=" -relet 2"
        cmdstr=cmdstr+"/var/tendatest/TDT/bin/dhcpd -cf /tmp/dhcpd.conf -lf /var/db/dhcpd.leases %s %s %s %s %s %s\n" %(self.if_name,lease_flag,opt33_args,opt121_args,opt249_args,ackstr)
        #print "cmdstr=",cmdstr
        if 'serv' not in conn_ssh:
            msg_box = qtm(qtm.Warning, "Alert", u"请先连接服务器!")
            msg_box.exec_()
            return
        else:
            for m in cmdstr.split('\n'):
                print "cmd_m=",m
                if m:
                    print "cmd_m=",m
                    stdin,stdout,stderr=conn_ssh['serv'].exec_command(m,timeout=20.0)
                    stdin.flush()
                    stdin.channel.shutdown_write()
                    ret=stdout.read()
                    err = stderr.read()
                    if ret:
                        print "ret=",ret
                    if err:
                        print "err=",err
            msg_box = qtm(qtm.Warning, "Alert", u"DHCP服务器配置成功!")   
        msg_box.exec_()
        stdin,stdout,stderr=conn_ssh['serv'].exec_command("pidof dhcpd",timeout=20.0)
        result = stdout.read()
        self.dhcpstatus = "running"
        if result != "":
            print "result=",result
            self.ui.serstatus.setText(u"服务器已开启")
            self.ui.save.setText(u"关闭服务器")
    def get_para(self):
        #读取控件值，并保存为全局变量    
        self.if_name=unicode(self.ui.if_name.text())
        self.if_ip=unicode(self.ui.if_ip.text())
        self.if_mask=unicode(self.ui.if_mask.text())
        self.start_ip=unicode(self.ui.start_ip.text())
        self.end_ip=unicode(self.ui.end_ip.text())
        self.gateway_ip=unicode(self.ui.gateway_ip.text())
        self.dns_ip=unicode(self.ui.dns_ip.text())
        self.lease_time=unicode(self.ui.lease_time.text())
        self.ack_checkbox=int(self.ui.ack_checkbox.isChecked())
        self.opt33_dst=unicode(self.ui.opt33_dst.text())
        self.opt33_next_hop=unicode(self.ui.opt33_next_hop.text())
        self.opt33_net = unicode(self.ui.opt33_net.text())
        self.opt121_dst=unicode(self.ui.opt121_dst.text())
        self.opt121_next_hop=unicode(self.ui.opt121_next_hop.text())
        self.opt121_net = unicode(self.ui.opt121_net.text())
        self.opt249_dst=unicode(self.ui.opt249_dst.text())
        self.opt249_next_hop=unicode(self.ui.opt249_next_hop.text())
        self.opt249_net = unicode(self.ui.opt249_net.text())
        id=self.ui.lnk_ip.currentIndex()  
        if id == 0:
            config['dhcpser0']['if_name']=self.if_name
            config['dhcpser0']['if_ip']
            config['dhcpser0']['if_mask']=self.if_mask
            config['dhcpser0']['start_ip']=self.start_ip
            config['dhcpser0']['end_ip']=self.end_ip
            config['dhcpser0']['gateway_ip']=self.gateway_ip
            config['dhcpser0']['dns_ip']=self.dns_ip
            config['dhcpser0']['lease_time']=self.lease_time
            config['dhcpser0']['ack_checkbox']=self.ack_checkbox
            config['dhcpser0']['opt33_dst']=self.opt33_dst
            config['dhcpser0']['opt33_next_hop']=self.opt33_next_hop
            config['dhcpser0']['opt33_net']=self.opt33_net
            config['dhcpser0']['opt121_dst']=self.opt121_dst
            config['dhcpser0']['opt121_next_hop']=self.opt121_next_hop
            config['dhcpser0']['opt121_net']=self.opt121_net
            config['dhcpser0']['opt249_dst']=self.opt249_dst
            config['dhcpser0']['opt249_next_hop']=self.opt249_next_hop
            config['dhcpser0']['opt249_net']=self.opt249_net
        elif id == 1:
            config['dhcpser1']['if_name']=self.if_name
            config['dhcpser1']['if_ip']
            config['dhcpser1']['if_mask']=self.if_mask
            config['dhcpser1']['start_ip']=self.start_ip
            config['dhcpser1']['end_ip']=self.end_ip
            config['dhcpser1']['gateway_ip']=self.gateway_ip
            config['dhcpser1']['dns_ip']=self.dns_ip
            config['dhcpser1']['lease_time']=self.lease_time
            config['dhcpser1']['ack_checkbox']=self.ack_checkbox
            config['dhcpser1']['opt33_dst']=self.opt33_dst
            config['dhcpser1']['opt33_next_hop']=self.opt33_next_hop
            config['dhcpser1']['opt33_net']=self.opt33_net
            config['dhcpser1']['opt121_dst']=self.opt121_dst
            config['dhcpser1']['opt121_next_hop']=self.opt121_next_hop
            config['dhcpser1']['opt121_net']=self.opt121_net
            config['dhcpser1']['opt249_dst']=self.opt249_dst
            config['dhcpser1']['opt249_next_hop']=self.opt249_next_hop
            config['dhcpser1']['opt249_net']=self.opt249_net            
        else:
            config['dhcpser2']['if_name']=self.if_name
            config['dhcpser2']['if_ip']
            config['dhcpser2']['if_mask']=self.if_mask
            config['dhcpser2']['start_ip']=self.start_ip
            config['dhcpser2']['end_ip']=self.end_ip
            config['dhcpser2']['gateway_ip']=self.gateway_ip
            config['dhcpser2']['dns_ip']=self.dns_ip
            config['dhcpser2']['lease_time']=self.lease_time
            config['dhcpser2']['ack_checkbox']=self.ack_checkbox
            config['dhcpser2']['opt33_dst']=self.opt33_dst
            config['dhcpser2']['opt33_next_hop']=self.opt33_next_hop
            config['dhcpser2']['opt33_net']=self.opt33_net
            config['dhcpser2']['opt121_dst']=self.opt121_dst
            config['dhcpser2']['opt121_next_hop']=self.opt121_next_hop
            config['dhcpser2']['opt121_net']=self.opt121_net
            config['dhcpser2']['opt249_dst']=self.opt249_dst
            config['dhcpser2']['opt249_next_hop']=self.opt249_next_hop
            config['dhcpser2']['opt249_net']=self.opt249_net            
        config.write()
    def load_para(self):
        ip = config['dhcpser']['lnk_ip']
        if self.ui.lnk_ip.count():
            self.ui.lnk_ip.clear()
        self.ui.lnk_ip.addItems(["A","B","C"])    
        self.ui.lnk_ip.setCurrentIndex(["A","B","C"].index(ip))
        self.ui.if_name.setText(config['dhcpser2']['if_name'])
        self.ui.if_ip.setText(config['dhcpser2']['if_ip'])
        self.ui.if_mask.setText(config['dhcpser2']['if_mask'])
        self.ui.start_ip.setText(config['dhcpser2']['start_ip'])
        self.ui.end_ip.setText(config['dhcpser2']['end_ip'])
        self.ui.gateway_ip.setText(config['dhcpser2']['gateway_ip'])
        self.ui.dns_ip.setText(config['dhcpser2']['dns_ip'])  
        self.ui.opt33_dst.setText(config['dhcpser2']['option33_dst'])
        self.ui.opt33_next_hop.setText(config['dhcpser2']['option33_next_hop'])
        self.ui.opt33_net.setText(config['dhcpser2']['option33_net'])
        self.ui.opt121_dst.setText(config['dhcpser2']['option121_dst'])
        self.ui.opt121_next_hop.setText(config['dhcpser2']['option121_next_hop'])
        self.ui.opt121_net.setText(config['dhcpser2']['option121_net'])
        self.ui.opt249_dst.setText(config['dhcpser2']['option249_dst'])
        self.ui.opt249_next_hop.setText(config['dhcpser2']['option249_next_hop'])
        self.ui.opt249_net.setText(config['dhcpser2']['option249_net'])        
        self.ui.lease_time.setText(config['dhcpser2']['lease_time'])
        if config['dhcpser2']['ack_checkbox'] == 1:
            self.ui.ack_checkbox.setChecked(config['dhcpser2']['ack_checkbox'])
        # self.ui.Cmd.setText(config['dhcpser']['self.Cmd'])
    def change_para(self):
        id=self.ui.lnk_ip.currentIndex()  
        if id == 0:
            self.ui.if_name.setText(config['dhcpser0']['if_name'])
            self.ui.if_ip.setText(config['dhcpser0']['if_ip'])
            self.ui.if_mask.setText(config['dhcpser0']['if_mask'])
            self.ui.start_ip.setText(config['dhcpser0']['start_ip'])
            self.ui.end_ip.setText(config['dhcpser0']['end_ip'])
            self.ui.gateway_ip.setText(config['dhcpser0']['gateway_ip'])
            self.ui.dns_ip.setText(config['dhcpser0']['dns_ip'])  
            self.ui.opt33_dst.setText(config['dhcpser0']['option33_dst'])
            self.ui.opt33_next_hop.setText(config['dhcpser0']['option33_next_hop'])
            self.ui.opt33_net.setText(config['dhcpser0']['option33_net'])
            self.ui.opt121_dst.setText(config['dhcpser0']['option121_dst'])
            self.ui.opt121_next_hop.setText(config['dhcpser0']['option121_next_hop'])
            self.ui.opt121_net.setText(config['dhcpser0']['option121_net'])
            self.ui.opt249_dst.setText(config['dhcpser0']['option249_dst'])
            self.ui.opt249_next_hop.setText(config['dhcpser0']['option249_next_hop'])
            self.ui.opt249_net.setText(config['dhcpser0']['option249_net'])
        elif id == 1:
            self.ui.if_name.setText(config['dhcpser1']['if_name'])
            self.ui.if_ip.setText(config['dhcpser1']['if_ip'])
            self.ui.if_mask.setText(config['dhcpser1']['if_mask'])
            self.ui.start_ip.setText(config['dhcpser1']['start_ip'])
            self.ui.end_ip.setText(config['dhcpser1']['end_ip'])
            self.ui.gateway_ip.setText(config['dhcpser1']['gateway_ip'])
            self.ui.dns_ip.setText(config['dhcpser1']['dns_ip'])  
            self.ui.opt33_dst.setText(config['dhcpser1']['option33_dst'])
            self.ui.opt33_next_hop.setText(config['dhcpser1']['option33_next_hop'])
            self.ui.opt33_net.setText(config['dhcpser1']['option33_net'])
            self.ui.opt121_dst.setText(config['dhcpser1']['option121_dst'])
            self.ui.opt121_next_hop.setText(config['dhcpser1']['option121_next_hop'])
            self.ui.opt121_net.setText(config['dhcpser1']['option121_net'])
            self.ui.opt249_dst.setText(config['dhcpser1']['option249_dst'])
            self.ui.opt249_next_hop.setText(config['dhcpser1']['option249_next_hop'])
            self.ui.opt249_net.setText(config['dhcpser1']['option249_net'])
        else:
            self.ui.if_name.setText(config['dhcpser2']['if_name'])
            self.ui.if_ip.setText(config['dhcpser2']['if_ip'])
            self.ui.if_mask.setText(config['dhcpser2']['if_mask'])
            self.ui.start_ip.setText(config['dhcpser2']['start_ip'])
            self.ui.end_ip.setText(config['dhcpser2']['end_ip'])
            self.ui.gateway_ip.setText(config['dhcpser2']['gateway_ip'])
            self.ui.dns_ip.setText(config['dhcpser2']['dns_ip'])  
            self.ui.opt33_dst.setText(config['dhcpser2']['option33_dst'])
            self.ui.opt33_next_hop.setText(config['dhcpser2']['option33_next_hop'])
            self.ui.opt33_net.setText(config['dhcpser2']['option33_net'])
            self.ui.opt121_dst.setText(config['dhcpser2']['option121_dst'])
            self.ui.opt121_next_hop.setText(config['dhcpser2']['option121_next_hop'])
            self.ui.opt121_net.setText(config['dhcpser2']['option121_net'])
            self.ui.opt249_dst.setText(config['dhcpser2']['option249_dst'])
            self.ui.opt249_next_hop.setText(config['dhcpser2']['option249_next_hop'])
            self.ui.opt249_net.setText(config['dhcpser2']['option249_net'])          
    def test_start(self):
        self.ui.textEdit_res.ensureCursorVisible()
        testcmd=unicode(self.ui.Cmd.text())
        qtm=QtGui.QMessageBox
        if main_para == {}:
            msg_box = qtm(qtm.Warning, "Alert", u"警告！！请先连接服务器并配置DNS服务器!")
        else:
             msg_box = qtm(qtm.Warning, "Alert", u"测试中，请稍后…………")
        msg_box.exec_() 
        if main_para['Cliip'] == '':
            os.popen('cmd')
            str='.'
            ip= str.join(main_para['Dutip'].split('.')[:-1])
            kcip='%s.111' %(ip)
            strcmd='netsh interface ip set address name="kc" static %s 255.255.255.0 %s\n' %(kcip,main_para['Dutip'])
            strcmd=strcmd+'netsh interface ip add dns "kc" %s index=1\n' %(self.DnsSer1)
            if self.DnsSer2 != '':
                strcmd=strcmd+'netsh interface ip add dns "kc" %s index=2\n' %(self.DnsSer2)
            for subcmd in strcmd.split('\n'):
                os.popen(subcmd)                
            #time.sleep(5)
            t=os.popen(testcmd)
            result=t.read().decode('gbk')
            print "ping result"
        else:
            if re.search('ping',testcmd):
                testcmd='%s -c 5' %(testcmd)
            #if 'cli' not in conn_ssh:
               # if self.parent.ssh_link(main_para['Cliip'],'root','tendatest'):
                    #stdin,stdout,stderr=conn_ssh['cli'].exec_command(testcmd)
            stdin,stdout,stderr=conn_ssh['cli'].exec_command(testcmd,timeout=20.0)
            result = stdout.read()     
            if not result:
                result = stderr.read()     
        self.ui.textEdit_res.setPlainText(result)
        r=unicode(self.ui.textEdit_res.toPlainText())
        self.ui.textEdit_res.ensureCursorVisible()
if __name__=="__main__":  
    app=QApplication(sys.argv)  
    form=DhcpSer()  
    form.show()  
    app.exec_() 