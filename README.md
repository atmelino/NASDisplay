# NASDisplay



on server:

pip install pyserial

pip install PySensors







<h2> Autostart Display script at Boot</h2>


    add the NASDisplay software as a service using systemd.<br>
    add file NASDisplay.service to /etc/systemd/system.<br>
    Start and stop:<br>
    <code>sudo systemctl start NASDisplay.service</code><br>
    <code>sudo systemctl stop NASDisplay.service</code><br>
    check status:<br>
    <code>sudo systemctl status NASDisplay.service</code><br>
    during development</code><br>
    <code>sudo systemctl daemon-reload</code><br>
    <code>sudo systemctl restart NASDisplay.service</code><br>
    To start automatically at boot:<br>
    <code>sudo systemctl enable NASDisplay.service</code><br>
    To list all services:<br>
    <code>sudo systemctl list-unit-files</code><br>
    or<br>
    <code>sudo systemctl list-unit-files | grep NASDisplay.service </code><br>
    To see output from service:<br>
    <code>journalctl -u NASDisplay.service -b</code><br>
    To shorten journal file:<br>
    <code>sudo journalctl --rotate</code><br>
    <code>sudo journalctl --vacuum-time=1s</code><br>





