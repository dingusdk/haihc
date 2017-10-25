# Introduction

This implement support for IHC in Home Assistant. The soap interfacing to IHC is done in this library

https://github.com/dingusdk/PythonIhcSdk

It should be installed automatically by home assistant from the PyPi.


# How to use it


**Option 1**

Download the git repository manually and copy the custom_components to the homeassistant configuration folder (the folder that contains your configuration yaml file) - so you have the "custom_components" folder as a sub folder to your HA configuration folder.

**Option 2** (for linux)

If you want to be able to get updates easier using git, it may be a good idea to keep the clone of the git repository in a separate folder, and then make a link to the custom_components folder.
Assuming you have a homeassistant user to run HA do like this:

```bash
cd ~
git clone https://github.com/dingusdk/haihc
```
You will now have a clone of the repository in a haihc folder in your home folder.
Now make the link the the custom_components folder
```bash
cd .homeassistant
ln -s /home/homeassistant/haihc/custom_components custom_components
```
later when you want to get updates from git do:
```bash
cd ~/haihc
git pull
```

**Configuration**

See the post on my blog for further description about how to configure it:

http://www.dingus.dk/home-assistant-ihc-integration/



# License

HAIhc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

HAIhc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HAIhc.  If not, see <http://www.gnu.org/licenses/>.

