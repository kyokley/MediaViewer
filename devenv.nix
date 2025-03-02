{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  # env.GREET = "MV";

  # https://devenv.sh/packages/
  # packages = [
  #   pkgs.git
  # ];

  # https://devenv.sh/scripts/
  # scripts.runtests.exec = "${pkgs.gnumake}/bin/make tests";

  # enterShell = ''
  #   # hello
  # '';

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
  };

  tasks."mv:format" = {
    exec = ''
      pwd
      ls -la
      ${config.git-hooks.installationScript}
      ${pkgs.pre-commit}/bin/pre-commit run -av --show-diff-on-failure
    '';
  };

  # https://devenv.sh/processes/
  # processes.ping.exec = "ping example.com";

  # See full reference at https://devenv.sh/reference/options/
}
