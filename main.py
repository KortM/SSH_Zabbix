from paramiko import SSHClient, AutoAddPolicy
import asyncio
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from bs4 import BeautifulSoup
import datetime

complete_host = []

async def connect(host: str, password: str,cs_cons_passwd:str, user: str, domain: str):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            username=user,
            password=password,
            port=22,
            allow_agent=False,
            look_for_keys=False
        )
        print("Подключен")
    except Exception as e:
        with open('logs.txt', 'ab') as logs:
            logs.write('Подключение не удалось: {} {} {}\n'.format(host, domain, e).encode('utf-8'))
            logs.close()
        #print(e)
    try:
        channel = client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5)
        channel.exec_command("cs_console\n")
        channel.send("en\n")
        channel.send('{}\n'.format(cs_cons_passwd))
        channel.send("conf t\n")
        channel.send("no snmp-server polling address\n")
        channel.send("no snmp-server polling udp-port\n")
        channel.send("no snmp-server\n")
        channel.send("snmp-server community GZPRM RO\n")
        channel.send("snmp-server polling address 127.0.0.1\n")
        channel.send("snmp-server polling udp-port 1161\n")
        channel.send("no snmp-server host 10.98.32.105 version 2c GZPRM\n")
        channel.send("no snmp-server host 10.98.32.106 version 2c GZPRM\n")
        channel.send("end\n")
        channel.send("wr\n")
        channel.send("exit\n")
        path = "/opt/snmp_monitoring/snmp_extend/get_days_until_local_cert_exp/"
        client.exec_command(f"mkdir -p {path}\n")
        sftp_client = client.open_sftp()
        sftp_client.put(f'assets/get_days_until_local_cert_exp.cron.bash', f'{path}get_days_until_local_cert_exp.cron.bash')
        sftp_client.put(f'assets/get_days_until_local_cert_exp.extend.bash', f'{path}get_days_until_local_cert_exp.extend.bash')  
        channel = client.get_transport().open_session()
        channel.exec_command(f'chmod 777 {path}get_days_until_local_cert_exp.cron.bash\n')
        client.exec_command(f'bash {path}get_days_until_local_cert_exp.cron.bash\n')
        client.exec_command(
                f'(crontab -l ; echo "0 0,12 * * * /bin/bash {path}get_days_until_local_cert_exp.cron.bash")| crontab -\n')
        client.exec_command("service cron start\n")
        client.exec_command("update-rc.d cron enable\n")
        client.exec_command("update-rc.d snmpd enable\n")

        client.exec_command('echo "agentaddress {}:161" > /etc/snmp/snmpd.conf\n'.format(host))
        with open('assets/snmpd.conf', 'r') as f:
            for line in f:
                client.exec_command('echo "{}" >> /etc/snmp/snmpd.conf\n'.format(line))
            f.close()
        client.exec_command("service snmpd restart\n")
        print('Завершено обновление: {}, {}'.format(host, domain))
        complete_host.append([host, domain])

        
    except Exception as e:
        with open('logs.txt', 'ab') as logs:
            logs.write('Обновление не удалось: {} {}\nОшибка:{}\n'.format(host, domain, e).encode('utf-8'))
            logs.close()

async def main():
    Tk().withdraw()
    input("Загрузите список хостов\n Для продолжения нажмите любую клавишу")
    hosts_html = askopenfilename()
    user = input("Имя пользователя: \n")
    password = input("Пароль:\n")
    cs_passwd = input("Пароль от cs_cons\n")
    with open(hosts_html, 'rb') as f:
        tmp = f.read()
        soup = BeautifulSoup(tmp, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')
        hosts = []
        for row in rows:
            cols = row.find_all('td')
            cols = [val.text.strip() for val in cols]
            hosts.append(cols)
        f.close()
        for host in hosts:
            print(f'Поставлен на обновление: {host[1]}, ip: {host[2]}')
            task = asyncio.create_task(
                connect(
                    host=host[2],
                    password=password,
                    user=user,
                    domain=host[1],
                    cs_cons_passwd=cs_passwd
                )
            )
        

asyncio.run(main())
print(f"Удачно обновлено: {len(complete_host)}")
input("Для завершения нажмите любую клавишу")