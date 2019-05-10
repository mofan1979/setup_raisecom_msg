import os
import logging
from telnetlib import Telnet  # 调用telnet方法需要的库
from datetime import datetime
import socket
from time import sleep

# 日志模块初始化
logger = logging.getLogger()  # 定义对应的程序模块名name，默认是root
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()  # 日志输出到屏幕控制台
ch.setLevel(logging.INFO)  # 设置日志等级
home = os.getcwd()
log_filename = os.path.join(home, 'result_%s.log' % datetime.now().strftime('%Y%m%d_%H%M'))
formatter = logging.Formatter("%(asctime)s - %(message)s\r\n", '%Y-%m-%d %H:%M:%S')  # 定义日志输出格式
# 指定输出格式
ch.setFormatter(formatter)
# 增加指定的handler
logger.addHandler(ch)


class Msg:
    def __init__(self, bn, ip, telnetuser, telnetpw):
        self.login_flag = False
        self.bn = bn
        self.ip = ip
        self.telnetuser = telnetuser
        self.telnetpw = telnetpw
        self.tn = Telnet()

    def login(self):
        try:
            self.tn.open(self.ip.encode(), port=23, timeout=3)
            # 登陆交互
            self.tn.write(b'\n')
            self.tn.expect([b'Username:'], timeout=2)
            self.tn.write(self.telnetuser.encode() + b'\n')
            self.tn.read_until(b'Password:', timeout=2)
            self.tn.write(self.telnetpw.encode() + b'\n')
            self.tn.read_until(b'>', timeout=2)
            self.tn.write('enable\n'.encode())
            if '#' in self.tn.read_until(b'#', timeout=2).decode("utf8", "ignore"):
                self.login_flag = True
                logging.info('%s login 成功', self.ip)
            else:
                logging.warning('%s login 失败，非raisecom设备或密码错误' % self.ip)
                self.logout()
                return '%s,login 失败，非raisecom设备或密码错误\n' % self.ip
        except socket.timeout:
            logging.warning('%s login 失败，设备不在线' % self.ip)
            return '%s,login 失败，设备不在线\n' % self.ip
        except EOFError:
            logging.warning('%s 连接断开，可能会话数已满' % self.ip)
            return '%s,连接断开，可能会话数已满\n' % self.ip

    def logout(self):
        try:
            self.tn.close()
            logging.info('%s logout 成功', self.ip)
        except:
            logging.warning('%s logout 错误', self.ip)

    # 检查型号和批次
    def mod_bn(self):
        self.login()
        if self.login_flag:
            try:
                # 读取版本
                self.tn.write('show version\n'.encode())
                msginfo = self.tn.read_until(b"#", timeout=2).decode("utf8", "ignore")
                if self.bn in msginfo:
                    logging.info('%s 批次号为 %s , 不需要修改', self.ip, self.bn)
                else:
                    self.tn.write('testnode\n'.encode())
                    self.tn.read_until(b"Password:", timeout=2)
                    self.tn.write('rcios.test\n'.encode())
                    self.tn.read_until(b"(test-node)#", timeout=2)
                    self.tn.write(('bn %s\n' % self.bn).encode())
                    self.tn.read_until(b"(test-node)#", timeout=2)
                    self.tn.write('end\n'.encode())
                    self.tn.read_until(b"#", timeout=2)
                    self.tn.write('erase startup-config\n'.encode())
                    self.tn.read_until(b"#", timeout=15)
                    self.tn.write('reboot\n'.encode())
                    # self.tn.read_until(b"confirm:", timeout=1)
                    sleep(1)
                    self.tn.write(b'y\n')
                    self.tn.read_until(b'#', timeout=5)
                    logging.info('%s 批次号已修改为 %s ，设备自动重启，如果设备没有自动重启，请手动重启设备生效', self.ip, self.bn)
                self.logout()
            except:
                logging.warning('%s 修改批次号错误', self.ip)
                self.logout()


if __name__ == '__main__':
    input('请确认电脑连接到设备的LAN 1口，能PING通地址192.168.1.1。按回车继续')
    msg2100 = Msg(bn='GX01', ip='192.168.1.1', telnetuser='telecomadmin', telnetpw='nE7jA%5m')
    msg2100.mod_bn()
    input('按回车退出')
