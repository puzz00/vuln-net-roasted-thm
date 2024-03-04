# hacking vulnnet:roasted (thm)

The **vulnnet:roasted** machine on [thm](https://tryhackme.com) gives us a great opportunity to mess around with active directory attacks.

---

## port scanning

We begin with an nmap scan of all the ports using tcp:

`ports64=$(sudo nmap -n -Pn -p- --min-rate=250 -sS --open 10.10.180.64 | grep ^[0-9] | cut -d '/' -f 1 -tr '\n' ',' | sed s/,$//)`

`echo $ports64 > p64.txt`

This shows us that port 88 is open which suggests that the target machine is a domain controller for a windows domain since port 88 is used by domain controllers for kerberos traffic.

![nmap scan result one](/images/1.png)

> [!NOTE]
> Domain Controllers are high value targets and must be pwned at all costs

A domain in windows is just a collection of objects such as users and computers which are administered together. Domains are used everywhere as they let organizations easily manage their assets and up scale if they want to.

Active directory is like a catalogue of all the objects in the domain and a domain controller is a server which runs active directory services. The long and short of this is this - domain controllers are high value targets as they contain lots of useful data (including password hashes 😈) for us to loot and mess with.

Domain controllers have port 88 open as this is the port which is used by kerberos. Kerberos :dog::dog::dog: is the main authorisation method used in active directory environments. The domain controller stores user data (including those password hashes :smiling_imp:) and therefore lots of authentication queries are made to the domain controller via kerberos over port 88.

We now try probing the open ports more using nmap:

`sudo nmap -Pn -n -p$ports64 -sV -A 10.10.180.64`

![nmap scan two](/images/2.png)

As is normal for a machine running windows, we see that smb is being used on port 445. It is usually a good idea to enumerate smb so this is what we will do next.

---

## smb enumeration

First of all, we can use smbclient to see if null sessions are allowed - we find that they are:

`sudo smbclient -N -L \\\\10.10.180.64\\`

![smbclient](/images/3.png)

We can find out more about the available shares using smbmap. Sometimes we don't need to specify any username:password combinations and we can retrieve data, but this time that won't work so we need to give the username *guest* and leave the password as a blank string. 

`sudo smbmap -H 10.10.180.64 -u "guest" -p ""`

Using this combo we see that we have read access to the IPC$ share along with two custom shares called *VulnNet-Business-Anonymous* and *VulNet-Enterprise-Anonymous*

![smbmap](/images/4.png)

Since it's always nice to know other tools 🛠️ that do the job, I tried using crackmapexec to have a look at the shares, too:

`sudo crackmapexec smb 10.10.212.255 -u "guest" -p "" --shares`

![crackmapexec one](/images/4b.png)

The IPC$ share is useful to have read access to as it is used to let anonymous users enumerate a domain. It is a good idea to use this to our advantage in order to try and find some valid usernames.

---

## enumerating usernames

We can use crackmapexec to do this using the `--rid-brute` switch:

`sudo crackmapexec smb 10.10.180.64 -u "guest" -p "" --rid-brute`
