# FATAL FLAW: Synchronous blocking call inside async def coroutine
response = requests.post("https://ci-runner.internal.corp/build", json={"repo": repo})
