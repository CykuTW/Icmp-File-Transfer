# Icmp File Transfer
# Send files using ICMP as the transport protocol. (ICMP/IP)

**A simple Proof of Concept to reliably transfer a file through ICMP**

## Usage:

```
  ./icmp.py recv <destination file> <remote address>
  ./icmp.py send <file to transfer> <remote address>
```

## Commands

```
  recv: 
    Listens for ICMP packets and tries to assemble them into a file and store it
    on <destination file> path.
 
  send:
    Reads <file to transfer> and sends it to <remote address> using the ICMP/IP
    stack.
```


## Description:
  Icmp File Transfer is a simple tool to test if a network user can exfiltrate information without being noticed using ICMP.
  
  It uses the data field of the ICMP ECHO REQUEST packets in order to hide this information.   

## Feature
- Make reliable using sequence number (Added by Cyku)

## Requirements

- root privilege

- Make sure the server can handle ICMP packet over 65000 Bytes.

  If it can't, modify `ICMP_PACKET_SIZE` in ICMP/IcmpPacket.py to suit your environment.
  ```
  root@server1:~# ping -s 65000 server2
  PING server2 (<ip>) 65000(65028) bytes of data.
  65008 bytes from server2 (<ip>): icmp_seq=1 ttl=55 time=206 ms
  65008 bytes from server2 (<ip>): icmp_seq=2 ttl=55 time=205 ms
  65008 bytes from server2 (<ip>): icmp_seq=3 ttl=55 time=204 ms
  ```

- Enough RAM

  The default size of window (buffer) for ICMP packet is 50. If your server doesn't have enough memory, modify `self.window_size` in ICMP/IcmpApp.py


## Test

Only tested to transfer a 100M file from a server in America (server1) to a server in Singapore (server2).

You can speed up the transmission by telling the Operating System to stop replying to all ICMP packets.

```
root@server2:~# echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_all
root@server2:~# cat /proc/sys/net/ipv4/icmp_echo_ignore_all
1
```

Make a 100M garbage file.

```
root@server1:~/icmp-file-transfer# dd if=/dev/urandom of=./file bs=1024 count=102400
root@server1:~$ ls -lah
total 101M
-rw-rw-r-- 1 root root 100M Feb 16 14:22 file
```

It costs about 26.082s to finish transmission in my environment.

Speed about 3.834 MB/s.

```
root@server1:~/icmp-file-transfer# time ./icmp.py send file server2
1616 / 1616

Finished

real    0m26.082s
user    0m21.854s
sys     0m0.519s

root@server2:~/icmp-file-transfer# time ./icmp.py send file server1
1616 / 1616

Finished
```

And the hashes of the files on both server are same.

```
root@server1:~/icmp-file-transfer# sha1sum file
8f5fe667b74c9e1fe9490f4ebfcbb00d32fdbf3a  file

root@server2:~/icmp-file-transfer# sha1sum file
8f5fe667b74c9e1fe9490f4ebfcbb00d32fdbf3a  file
```

## Original author
  Daniel Vidal de la Rubia.


## Bugs
  https://github.com/CykuTW/Icmp-File-Transfer/issues


## See also
  http://vidimensional.wordpress.com/2013/06/21/sending-files-through-icmp/

