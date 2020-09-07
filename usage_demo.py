from octomachinery.app.config import BotAppConfig
from octomachinery.app.github import GitHubApplication
from octomachinery.routing.routers import ConcurrentRouter


router1 = ConcurrentRouter()  # .on and other helpers?

app1 = GitHubApplication(
    event_routers={router1},
    config=BotAppConfig.from_dotenv(),
)


# process many events arriving over HTTP:
__name__ == '__main__' and app1.start()
# FIXME: use variants?
# await app1.serve_forever()  # ? == app1.start()?  <- Probot

# NOTE: Depending on whether the API is for external or internal use,
# NOTE: its semantics may feel different. What for external caller is
# NOTE: "send event into the system", for internals would be "dispatch/
# NOTE: handle the received event".
# process a single event:
# await app1.dispatch_event(event)  # ? == await app1.receive(event)  <- Probot
# [BAD] await app1.simulate_event(event)?  <-- tests?  FIXME: have a pytest fixture called `simulate_event`?
