from fake_headers import Headers

def rHeader(referrer=''):
    header = Headers(
        browser="chrome",  # Generate only Chrome UA
        os="win",  # Generate ony Windows platform
        headers=False,  # generate misc headers
    )
    header = header.generate()
    header['referer'] = ''
    header['connection'] = 'close'
    return header