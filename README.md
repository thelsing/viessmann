# Viessmann

Requirements
============
This plugin needs an running vcontrold server (my modified version).
Currently only reading data from vcontrold is supported.

Configuration
=============

plugin.conf
-----------
<pre>
[Viessmann]
    class_name = Viessmann
    class_path = plugins.viessmann
    cycle = 300
#    host = '127.0.0.1'
#    port = 3002
</pre>

This plugins is looking by default for the vcontrold on 127.0.0.1 port 3002. You could change this in your plugin.conf.

Advanced options in plugin.conf. Please be careful.

* 'cycle' = timeperiod between two sensor cycles.

items.conf
--------------

### vcontrold_cmd
'vcontrold_cmd' defines the command to execute in vcontrold

<pre>
[Heizung]
    [[Aussentemperatur]]
        type = num
        vcontrold_cmd = get_TiefpassTemperaturwert_ATS
</pre>
