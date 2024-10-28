def parse_sip_message(sip_message: str):
    # Split the message into headers and SDP body
    parts = sip_message.split("\r\n\r\n", 1)
    if len(parts) != 2:
        return None, None

    headers_part = parts[0]
    sdp_part = parts[1]

    # Split headers into lines and remove any empty lines
    headers_lines = [line for line in headers_part.split("\r\n") if line.strip()]

    # Shift out the first line as the Request-Line
    if len(headers_lines) == 0:
        return

    request_line = headers_lines.pop(0)

    # Parse remaining headers into a dictionary
    headers = {"request-line": request_line.lower()}

    for line in headers_lines:
        if ": " in line:
            name, value = line.split(": ", 1)
            if name is not None and value is not None:
                headers[name.lower()] = value.lower()

    return headers, sdp_part


def build_200_ok_response(invite_message, sdp_answer):
    headers, sdp = parse_sip_message(invite_message)
    via = headers["via"]
    call_id = headers["call-id"]
    to_header = headers["to"]
    from_header = headers["from"]
    cseq = headers["cseq"]
    contact = headers["contact"]

    # Build 200 OK response
    response = (f"SIP/2.0 200 OK\r\n"
                f"Via: SIP/2.0/UDP {via};branch=z9hG4bK776asdhds\r\n"
                f"To: {to_header}\r\n"
                f"From: {from_header}\r\n"
                f"Call-ID: {call_id}\r\n"
                f"CSeq: {cseq}\r\n"
                f"Contact: {contact}>\r\n"
                f"Content-Length: {len(sdp_answer)}\r\n\r\n"
                f"{sdp_answer}")

    return response
