#!/bin/bash

function systemctlInstalled {

    echo "systemctl is installed!"

    cp /opt/RpiCpuFan/RpiCpuFan /etc/init.d/
    chmod 755 /etc/init.d/RpiCpuFan

    systemctl daemon-reload
    systemctl enable RpiCpuFan.service
    systemctl start RpiCpuFan.service

}

function systemctlNotInstalled {

    echo "systemctl is NOT installed!"

    cp /opt/RpiCpuFan/RpiCpuFan /etc/init.d/
    chmod 755 /etc/init.d/RpiCpuFan

    update-rc.d RpiCpuFan enable
    service RpiCpuFan start
    
}

if [ `command -v systemctl` ]
then
    systemctlInstalled
else
    systemctlNotInstalled
fi

