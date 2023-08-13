import sys
import os

import anyio

import dagger


config = dagger.Config(log_output=sys.stdout)

async def run_cmd(image, cmd, context_dir, services=None):
    container = (
        image
        .with_env_variable("DJANGO_SETTINGS_MODULE", "mysite.docker_settings")
        .with_env_variable("WAITER_PASSWORD_HASH", os.environ.get("WAITER_PASSWORD_HASH", ""))
        .with_directory("/code", context_dir)
    )

    if services:
        for name, service in services.items():
            container = container.with_service_binding(name, service)

    container = container.with_exec(["sh", "-c", cmd])
    await container.stdout()

async def test():
    build_event = anyio.Event()

    async with dagger.Connection(config) as dagger_client:
        context_dir = dagger_client.host().directory(".")

        image = await _build(dagger_client, build_event, 'dev')
        await build_event.wait()

        # create postgres DB
        postgres = (
            dagger_client.container()
            .from_("postgres")
            .with_mounted_cache("/var/lib/postgresql/data", dagger_client.cache_volume("postgres-data"))
            .with_env_variable("POSTGRES_PASSWORD", "postgres")
            .with_env_variable("POSTGRES_HOST_AUTH_METHOD", "trust")
            .with_exposed_port(5432)
        )

        db_services = {'postgres': postgres}

        # when this block exits, all tasks will be awaited (i.e., executed)
        async with anyio.create_task_group() as tg:
            for cmd, services in (
                ('/venv/bin/pytest', db_services),
                ('/venv/bin/bandit -x ./mediaviewer/tests -r .', None),
                ('/venv/bin/python manage.py makemigrations --check', db_services),
            ):
                tg.start_soon(run_cmd, image, cmd, context_dir, services)


async def publish():
    # create Dagger client
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        context_dir = client.host().directory(".")

        user = os.environ['DOCKER_USER']

        # set secret as string value
        secret = client.set_secret("password", os.environ['DOCKER_PASSWORD'])

        image = await context_dir.docker_build(target='prod')

        addr = await image.with_registry_auth(
            "docker.io", user, secret
        ).publish(f"{user}/mediaviewer")

        print(f"Published at: {addr}")


async def build(target='prod'):
    event = anyio.Event()

    async with dagger.Connection(config) as dagger_client:
        await _build(dagger_client, event, target)
        await event.wait()


async def _build(dagger_client, event, target='prod'):
    # set build context
    context_dir = dagger_client.host().directory(".")

    # build using Dockerfile
    # publish the resulting container to a registry
    image_ref = await context_dir.docker_build(target=target)
    event.set()
    return image_ref


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[-1].lower() == 'publish':
            anyio.run(publish)
        elif sys.argv[-1].lower() == 'test':
            anyio.run(test)
    else:
        anyio.run(build)
