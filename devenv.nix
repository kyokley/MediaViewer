{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  # https://devenv.sh/basics/
  env = {
    MV_NAME = "mv";
    MV_HOST = "localhost";
    MV_USER = "dbuser";
    DJANGO_SETTINGS_MODULE = "mysite.settings";
    WAITER_PASSWORD_HASH = "";
    SKIP_LOADING_TVDB_CONFIG = 1;
    MV_STATIC_DIR = "static";
    MV_NPM_STATIC_DIR = "node_modules";
    MV_DEBUG = "true";
    MV_ALLOWED_HOSTS = "127.0.0.1,localhost";
    MV_WAITER_DOMAIN = "localhost:5000";
  };

  # https://devenv.sh/packages/
  packages = [
    pkgs.postgresql
    pkgs.node2nix
  ];

  # https://devenv.sh/scripts/
  scripts = {
    help.exec = ''
      echo Scripts
      devenv info | awk /scripts/ RS="\n\n" ORS="\n\n" | tail -n "+2" | sort | awk '{$3=""; print $0}'
    '';
    build.exec = ''
      nix build '.#mv-image'
      docker load < result
    '';
    clear.exec = ''
      rm -rf $DEVENV_STATE/postgres
    '';

    init.exec = ''
      down
      clear
      migrate
    '';

    _wait_for_db.exec = ''
      devenv up -d postgres
      ${pkgs.wait4x}/bin/wait4x postgresql 'postgres://${config.env.MV_USER}:${config.env.MV_USER}@${config.env.MV_HOST}:5432/${config.env.MV_NAME}?sslmode=disable'
    '';

    migrate.exec = ''
      _wait_for_db
      uv run python manage.py migrate
    '';

    up.exec = ''
      _wait_for_db
      uv run python manage.py collectstatic --no-input
      uv run python manage.py runserver 0.0.0.0:8000
    '';

    docker-up.exec = ''
      build
      _wait_for_db
      migrate
      docker run --rm \
                 -it \
                 --net host \
                 -e MV_NAME=${config.env.MV_NAME} \
                 -e MV_HOST=${config.env.MV_HOST} \
                 -e MV_USER=${config.env.MV_USER} \
                 -e SKIP_LOADING_TVDB_CONFIG=1 \
                 -e DJANGO_SETTINGS_MODULE="mysite.settings" \
                 kyokley/mediaviewer
    '';

    down.exec = ''
      devenv processes down
    '';

    pytest.exec = ''
      set -e
      _wait_for_db
      uv run pytest $(test $# -eq 0 && echo "-n 4" || echo $@)
      down
    '';

    check-migrations.exec = ''
      _wait_for_db
      uv run python manage.py makemigrations --check
      down
    '';

    bandit.exec = ''
      uv run bandit -x ./mediaviewer/tests,./.venv,./.devenv* $(test $# -eq 0 && echo "-r ." || echo $@)
    '';
  };

  enterShell = ''
    echo
    ${pkgs.figlet}/bin/figlet -f slant MediaViewer | ${pkgs.lolcat}/bin/lolcat
    echo
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    set -e
    check-migrations
    pytest
    bandit
  '';

  # https://devenv.sh/services/
  services.postgres = {
    enable = true;
    listen_addresses = "localhost";
    initialScript = ''
      CREATE ROLE ${config.env.MV_USER} WITH LOGIN PASSWORD '${config.env.MV_USER}' SUPERUSER;
    '';
    initialDatabases = [
      {
        name = config.env.MV_NAME;
        user = config.env.MV_USER;
      }
    ];
  };

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    version = "3.13";
    uv = {
      enable = true;
    };
  };

  # https://devenv.sh/pre-commit-hooks/
  git-hooks.hooks = {
    alejandra.enable = true;
    hadolint.enable = false;
    check-merge-conflicts.enable = true;
    check-added-large-files.enable = true;
    check-toml.enable = true;
    check-yaml.enable = true;
    checkmake.enable = true;
    detect-private-keys.enable = true;
    ripsecrets.enable = true;
    ruff.enable = true;
    ruff-format.enable = true;
    trim-trailing-whitespace.enable = true;
    yamlfmt.enable = true;
    yamllint.enable = false;
    prettier = {
      enable = true;
      files = "\\.js$";
      excludes = [
        "mediaviewer/static/passwordless/passwordless.v1.1.0.umd.min.js"
      ];
    };
    djlint = {
      enable = true;
      files = "\\.html$";
      stages = ["pre-commit"];
      pass_filenames = true;
      entry = "${pkgs.djlint}/bin/djlint --reformat";
    };

    bandit = {
      enable = true;
      name = "bandit-security-checks";
      entry = "${pkgs.uv}/bin/uvx bandit -c ${config.devenv.root}/pyproject.toml";
      files = "\\.py$";
      stages = ["pre-commit"];
      pass_filenames = true;
    };
  };

  # See full reference at https://devenv.sh/reference/options/
}
