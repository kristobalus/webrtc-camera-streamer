
from sip_parser import parse_sip_message

# Example SIP INVITE message
sip_message = """INVITE sip:user@example.com SIP/2.0
Via: SIP/2.0/UDP pc33.example.com;branch=z9hG4bK776asdhds
Max-Forwards: 70
To: <sip:user@example.com>
From: "Caller Name" <sip:caller@example.com>;tag=1928301774
Call-ID: a84b4c76e66710@pc33.example.com
CSeq: 314159 INVITE
Contact: <sip:caller@pc33.example.com>
Content-Type: application/sdp
Content-Length: 204\r\n\r\n
v=0
o=caller 53655765 2353687637 IN IP4 pc33.example.com
s=Session
c=IN IP4 203.0.113.1
t=0 0
m=audio 49170 RTP/AVP 0
a=rtpmap:0 PCMU/8000
m=video 51372 RTP/AVP 31
a=rtpmap:31 H261/90000
"""

# Parse the SIP message
headers, sdp = parse_sip_message(sip_message)

# Display parsed headers
if headers:
    print("Parsed SIP Headers:")
    for key, value in headers.items():
        print(f"{key}: {value}")
else:
    print("No headers found.")

# Display SDP part
if sdp:
    print("\nParsed SDP Body:")
    print(sdp)
else:
    print("No SDP found.")