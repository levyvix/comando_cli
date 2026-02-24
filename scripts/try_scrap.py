from scrapling.fetchers import StealthyFetcher

tree = StealthyFetcher.fetch(url="https://comando.la/", solve_cloudflare=True)

print(tree.body.decode("utf-8"))
