import docker

client = docker.from_env()

for cnt in client.containers.list(all = True):
    print(cnt.short_id, cnt.status, cnt.name)
