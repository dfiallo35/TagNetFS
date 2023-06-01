import rpyc

conn = rpyc.connect('localhost', 12345)
dns_service = conn.root.DNSService()
result = dns_service.query('example.com')
print(result)