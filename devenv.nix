{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  # https://devenv.sh/basics/
  env = {
    DJANGO_SETTINGS_MODULE = "mysite.docker_settings";
    WAITER_PASSWORD_HASH = "";
    MV_WEB_ROOT = "/www";
    SKIP_LOADING_TVDB_CONFIG = 1;
    MV_HOST = "localhost";
  };

  # https://devenv.sh/packages/
  packages = [
    pkgs.postgresql
  ];

  # https://devenv.sh/scripts/
  scripts = {
    help.exec = ''
      echo Scripts
      devenv info | awk /scripts/ RS="\n\n" ORS="\n\n" | tail -n "+2" | sort | awk '{$3=""; print $0}'
    '';
    runtests.exec = "${pkgs.gnumake}/bin/make tests";
    touch-history.exec = "touch .mv.history";
    build.exec = ''
      docker build \
        $(test ''${USE_HOST_NET:=0} -ne 0 && echo "--network=host" || echo "") \
        $(test ''${NO_CACHE:=0} -ne 0 && echo "--no-cache" || echo "") \
        --build-arg UID=''${UID:=1000} \
        --tag=kyokley/mediaviewer \
        --target=prod \
        .
    '';
    build-dev.exec = ''
      docker build \
        $(test ''${USE_HOST_NET:=0} -ne 0 && echo "--network=host" || echo "") \
        $(test ''${NO_CACHE:=0} -ne 0 && echo "--no-cache" || echo "") \
        --build-arg UID=''${UID:=1000} \
        --tag=kyokley/mediaviewer \
        --target=dev \
        .
    '';
    pytest.exec = ''
      ${pkgs.docker}/bin/docker compose run --rm mediaviewer pytest -n 4
    '';
    shell.exec = ''
      ${pkgs.docker}/bin/docker compose run --rm mediaviewer bash
    '';
    down.exec = ''
      ${pkgs.docker}/bin/docker compose down --remove-orphans
    '';
    clear.exec = ''
      ${pkgs.docker}/bin/docker compose down --remove-orphans -v
    '';

    init.exec = ''
      rm -r $DEVENV_STATE/postgres
      devenv up -d postgres
      sleep 3
      nix run . -- migrate
      devenv down
    '';
  };

  enterShell = ''
    echo
    ${pkgs.figlet}/bin/figlet -f slant MediaViewer | ${pkgs.lolcat}/bin/lolcat
    echo
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    ${pkgs.gnumake}/bin/make tests
  '';

  # https://devenv.sh/services/
  services.postgres = {
    enable = true;
    initialDatabases = [{name = "postgres";}];
    initialScript = ''
      CREATE ROLE postgres SUPERUSER;
    '';
    listen_addresses = "localhost";
  };

  # https://devenv.sh/languages/
  # languages.nix.enable = true;
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

  tasks."mv:format" = {
    exec = ''
      ${config.git-hooks.installationScript}
      ${pkgs.pre-commit}/bin/pre-commit run --all-files --show-diff-on-failure
    '';
  };

  # https://devenv.sh/processes/
  processes = {
    # ping.exec = "ping example.com";
    server = {
      exec = "nix run . -- runserver";
      # cwd = "./public";
    };
  };

  # See full reference at https://devenv.sh/reference/options/
}
