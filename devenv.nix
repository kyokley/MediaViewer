{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  # https://devenv.sh/basics/
  env = {
    MV_NAME = lib.mkDefault "mv";
    MV_HOST = lib.mkDefault "localhost";
    MV_USER = lib.mkDefault "dbuser";
    DJANGO_SETTINGS_MODULE = "config.settings";
    MV_WAITER_PASSWORD_HASH = "";
    MV_SKIP_LOADING_TVDB_CONFIG = 1;
    MV_STATIC_DIR = "static";
    MV_NPM_STATIC_DIR = "node_modules";
    MV_DEBUG = "true";
    MV_ALLOWED_HOSTS = "127.0.0.1,localhost";
    MV_WAITER_DOMAIN = "localhost:5000";
  };

  # https://devenv.sh/packages/
  packages = [
    pkgs.postgresql
    pkgs.nodejs_25
  ];

  # https://devenv.sh/scripts/
  scripts = {
    frontend-run.exec = ''
      cd frontend && npm run dev
    '';

    help.exec = ''
      echo Scripts
      devenv info | awk /scripts/ RS="\n\n" ORS="\n\n" | tail -n "+2" | sort | awk '{$3=""; print $0}'
    '';

    list.exec = ''
      devenv info | awk /scripts/ RS="\n\n" ORS="\n\n" | tail -n "+2" | sort
    '';

    _touch-history.exec = ''
      touch .mv.history
    '';

    build.exec = ''
      set -x
      _touch-history
      nix build '.#mv-image'
      docker load < result
    '';

    build-dev.exec = ''
      set -x
      _touch-history
      nix build '.#dev-image'
      docker load < result
    '';

    up.exec = ''
      set -x
      ${pkgs.docker}/bin/docker compose up $@
    '';

    down.exec = ''
      set -x
      ${pkgs.docker}/bin/docker compose down $@
    '';

    logs.exec = ''
      ${pkgs.docker}/bin/docker compose logs $@
    '';

    shell.exec = ''
      build-dev
      ${pkgs.docker}/bin/docker compose run $@ bash
    '';

    attach.exec = ''
      ${pkgs.docker}/bin/docker compose attach $@
    '';

    clear.exec = ''
      ${pkgs.docker}/bin/docker compose down --remove-orphans -v
    '';

    init.exec = ''
      down
      clear
      migrate
    '';

    migrate.exec = ''
      uv run python manage.py migrate
    '';

    pytest.exec = ''
      set -e
      uv run pytest $(test $# -eq 0 && echo "-n 4" || echo $@)
      down
    '';

    check-migrations.exec = ''
      set -x
      uv run python manage.py makemigrations --check
      down
    '';

    bandit.exec = ''
      uv run bandit -x ./mediaviewer/tests,./.venv,./.devenv* $(test $# -eq 0 && echo "-r ." || echo $@)
    '';

    stop-all-but-db.exec = ''
      devenv processes down
      db-up
    '';

    static.exec = ''
      yarn install
    '';

    push.exec = ''
      build
      docker push kyokley/mediaviewer
    '';

    publish.exec = ''
      push
    '';

    autoformat.exec = ''
      uv run black .
      uv run isort .
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
