import dns.resolver
import dns.update

def set_dns_record(domain, ip_address):
    # create a resolver object
    resolver = dns.resolver.Resolver()

    # query the DNS server for the current SOA record
    soa_query = resolver.resolve(domain, 'SOA')

    # get the primary DNS server from the SOA record
    primary_dns = str(soa_query[0].mname)

    # create an update object
    update = dns.update.Update(domain, keyring=None, keyalgorithm=None)

    # add the new A record to the update object
    update.add(domain, 300, 'A', ip_address)

    # send the update to the primary DNS server
    response = dns.query.tcp(update, primary_dns)

    return response

set_dns_record('paco.com', '127.0.0.1')