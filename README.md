# Grand Route Dispatch
Grand Route Dispatch is a python script for routing specific url to Wi-Fi or Ethernet.  
This tool is helpful when your company limit access of internal ressources to Ethernet and limit certain services to wifi.

**GRD WORKS ONLY ON OS X & LINUX!**

## How it works
For example, imagine you need to plug your Ethernet cable in order to:  

* Print  
* Connect to LDAP  
* Access internal support websites  
* ...  

But you can't use Ethernet for streaming music or using dropbox.  
You just need to create your own hosts list then give it to GRD and it will automatically create route for you.  
NB: Routes will vanish when disconnect Wi-Fi and Ethernet

## Create your hosts file
There is only two specific tags.
First, `!wifi` every URLs after this tag and before next one (or EOF) will be routed to Wi-Fi.  
Next one is `!ethernet`, every URLs after this tag until EOF or another tag will be routed to Ethernet.  
Empty lines, wrong URLs and lines starting with `#` will be omitted.  
See [example](## Host list example)

## Download & use it!
* First, git clone it!  
`git clone https://github.com/Miasma87/grand-route-dispatch.git`
* Make it executable  
`chmod +x grand-route-dispatch.py`
* Launch it!  
`sudo ./grand-route-dispatch.py`

N.B: You should launch it with super-user privileges as `route` command need it.

## Configuration
First of all you will need to write a file listing all the URLs you want to dispatch.  
See [Host list example](## Host list example) for file example.

## Host list example
```
!wifi
# Here we will have URLs that will need to be redirected to Wi-Fi
google.com
spotify.com

!ethernet
# Here we will have URLs that will need to be redirected to Ethernet
ldap.yourcompany.com
webmail.yourcompany.com
# Printer IP
10.10.10.10
```

## Help
```
./grand-route-dispatch.py -h
usage: grand-route-dispatch.py [-h] [-f HOSTSFILE] [-d]

Grand Route Dispatch is a python script for routing specific url to Wi-Fi or
Ethernet.

optional arguments:
  -h, --help            show this help message and exit
  -f HOSTSFILE, --hostsfile HOSTSFILE
                        use given hosts file
  -d, --debug           pretty print debug info
```

## Known bugs nor issues
Not yet 🍻

## Known limitations
- Only works with OSX and Linux, for now
- Only works if the two devices are Wi-Fi and Thunderbolt Ethernet
- Wi-Fi need to be upper Thunderbolt Ethernet in "Service Order"

## Future features
- Support Windows (Pull requests are welcome)

## Thanks
I would like to thanks [ofaurax](https://github.com/ofaurax) for being the bootstrap of this project!

# Changelog
## 1.1 - 2015-12-06
### Added
- Linux support

## 1.0 - 2015-12-03
- First commit
- Support OS X only for now