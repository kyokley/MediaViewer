import sys
import os

import anyio

import dagger


DAGGER_CONFIG = dagger.Config(log_output=sys.stdout)


def build_image(dagger_client, target='prod'):
    # set build context
    context_dir = dagger_client.host().directory(".")

    # build using Dockerfile
    # publish the resulting container to a registry
    image = context_dir.docker_build(target=target)
    return image


async def run_cmd(dagger_client, image, cmd, services=None):
    context_dir = dagger_client.host().directory(".")

    container = (
        image
        .with_env_variable("DJANGO_SETTINGS_MODULE", "mysite.docker_settings")
        .with_env_variable("WAITER_PASSWORD_HASH", os.environ.get("WAITER_PASSWORD_HASH", ""))
        .with_directory("/code", context_dir)
    )

    if services:
        for service, container in services.items():
            container = container.with_service_binding(service, container)

    container = container.with_exec(["sh", "-c", cmd])
    await container.stdout()


async def run_tests(dagger_client, image, pytest=True, bandit=True, makemigrations=True):
    # create postgres DB
    postgres = (
        dagger_client.container()
        .from_("postgres")
        .with_mounted_cache("/var/lib/postgresql/data", dagger_client.cache_volume("postgres-data"))
        .with_env_variable("POSTGRES_PASSWORD", "postgres")
        .with_env_variable("POSTGRES_HOST_AUTH_METHOD", "trust")
        .with_exposed_port(5432)
    )

    tests = []

    if pytest:
        pytest_services = {'postgres': postgres}

        tests.append(
            ('/venv/bin/pytest', pytest_services),
        )

    if bandit:
        tests.append(
            ('/venv/bin/bandit -x ./mediaviewer/tests -r .', None),
        )

    if makemigrations:
        makemigrations_services = {'postgres': postgres}
        tests.append(
            ('/venv/bin/python manage.py makemigrations --check', makemigrations_services),
        )

    # when this block exits, all tasks will be awaited (i.e., executed)
    async with anyio.create_task_group() as tg:
        for cmd, services in tests:
            tg.start_soon(run_cmd, dagger_client, image, cmd, services)


async def publish_image(dagger_client, image, label='mediaviewer'):
    user = os.environ['DOCKER_USER']

    # set secret as string value
    secret = dagger_client.set_secret("password", os.environ['DOCKER_PASSWORD'])

    # use secret for registry authentication
    addr = await image.with_registry_auth(
        "docker.io", user, secret
    ).publish(f"{user}/{label}")

    print(f'Successfully pushed {addr}')


async def main(publish=False):
    async with dagger.Connection(DAGGER_CONFIG) as dagger_client:
        image = await build_image(dagger_client, 'dev').sync()
        await run_tests(dagger_client, image)

        if publish:
            image = await build_image(dagger_client, 'prod')
            await publish_image(dagger_client, image)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[-1].lower() == 'publish':
        anyio.run(main, True)
    else:
        anyio.run(main)
