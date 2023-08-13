import sys
import os

import anyio

import dagger


config = dagger.Config(log_output=sys.stdout)
async def main():
    async with dagger.Connection(config) as client:
        # set build context
        context_dir = client.host().directory(".")

        # build using Dockerfile
        # publish the resulting container to a registry
        image_ref = await context_dir.docker_build()

        # create postgres DB
        postgres = (
            client.container()
            .from_("postgres")
            .with_mounted_cache("/var/lib/postgresql/data", client.cache_volume("postgres-data"))
            .with_env_variable("POSTGRES_PASSWORD", "postgres")
            .with_env_variable("POSTGRES_HOST_AUTH_METHOD", "trust")
            .with_exposed_port(5432)
        )

        async def run_cmd(cmd):
            container = (
                image_ref
                .with_env_variable("DJANGO_SETTINGS_MODULE", "mysite.docker_settings")
                .with_env_variable("WAITER_PASSWORD_HASH", os.environ.get("WAITER_PASSWORD_HASH"))
                .with_directory("/code", context_dir)
                .with_service_binding("postgres", postgres)
                .with_exec(["sh", "-c", cmd])
            )
            await container.stdout()

        # when this block exits, all tasks will be awaited (i.e., executed)
        async with anyio.create_task_group() as tg:
            tg.start_soon(run_cmd, '/venv/bin/pytest -vx')

    print(f"Published image to: {image_ref}")


anyio.run(main)
