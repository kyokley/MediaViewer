{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  # https://devenv.sh/basics/
  # env.GREET = "MV";

  # https://devenv.sh/packages/
  packages = [
    pkgs.postgresql
  ];

  # https://devenv.sh/scripts/
  scripts = {
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
  # services.postgres.enable = true;

  # https://devenv.sh/languages/
  # languages.nix.enable = true;
  languages.python = {
    enable = true;
    version = "3.12";
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
  # processes.ping.exec = "ping example.com";

  # See full reference at https://devenv.sh/reference/options/
}
