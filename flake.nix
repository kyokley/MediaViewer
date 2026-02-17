{
  description = "Mediaviewer Python App with Nix and uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    # Core pyproject-nix ecosystem tools
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
      };
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};
        python = pkgs.python312; # Your desired Python version

        # 1. Load Project Workspace (parses pyproject.toml, uv.lock)
        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.; # Root of your flake/project
        };

        # 2. Generate Nix Overlay from uv.lock (via workspace)
        uvLockedOverlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel"; # Or "sdist"
        };

        # 3. Placeholder for Your Custom Package Overrides
        myCustomOverrides = final: prev: {
          # e.g., some-package = prev.some-package.overridePythonAttrs (...); */
          pytest-random = prev.pytest-random.overrideAttrs (old: {
            buildInputs = (old.buildInputs or []) ++ final.resolveBuildSystem {setuptools = [];};
          });
        };

        # 4. Construct the Final Python Package Set
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {inherit python;})
          .overrideScope (nixpkgs.lib.composeManyExtensions [
          pyproject-build-systems.overlays.default # For build tools
          uvLockedOverlay # Your locked dependencies
          myCustomOverrides # Your fixes
        ]);

        # --- This is where your project's metadata is accessed ---
        projectNameInToml = "mediaviewer"; # MUST match [project.name] in pyproject.toml!
        thisProjectAsNixPkg = pythonSet.${projectNameInToml};
        # ---

        # 5. Create the Python Runtime Environment
        appPythonEnv =
          pythonSet.mkVirtualEnv
          (thisProjectAsNixPkg.pname + "-env")
          workspace.deps.default; # Uses deps from pyproject.toml [project.dependencies]
        devPythonEnv =
          pythonSet.mkVirtualEnv
          (thisProjectAsNixPkg.pname + "-env")
          workspace.deps.all;

        # Node/NPM stuff
        inherit (pkgs.callPackage ./default.nix {}) nodeDependencies;

        packageBuildPhase = ''
          export MV_SKIP_LOADING_TVDB_CONFIG=1
          export MV_STATIC_DIR=$(pwd)/temp_static
          export MV_NPM_STATIC_DIR=${nodeDependencies}/lib/node_modules
          export MV_WAITER_DOMAIN=localhost
          export PYTHONPATH=$(pwd)
          export DJANGO_SETTINGS_MODULE=config.settings

          ${appPythonEnv}/bin/manage collectstatic --noinput
        '';
      in {
        # Development Shell
        devShells.default = pkgs.mkShell {
          packages = [devPythonEnv];
          shellHook = ''# Your custom shell hooks */ '';
        };

        # Nix Package for Your Application
        packages = {
          default = pkgs.stdenv.mkDerivation {
            inherit (thisProjectAsNixPkg) pname version;
            src = ./.; # Source of your main script

            nativeBuildInputs = [pkgs.makeWrapper];
            buildInputs = [appPythonEnv]; # Runtime Python environment

            buildPhase = packageBuildPhase;
            installPhase = ''
              mkdir -p $out/bin $out/lib

              cp ./gunicorn.conf.py $out/lib/
              cp -r ./temp_static $out/lib/static

              makeWrapper ${appPythonEnv}/bin/gunicorn $out/bin/mv-gunicorn \
                --add-flags "--config=$out/lib/gunicorn.conf.py" \
                --add-flags config.wsgi

              makeWrapper ${devPythonEnv}/bin/manage $out/bin/manage \
                --set PYTHONPATH $out/lib/mediaviewer \
                --set MV_DEBUG true \
                --set MV_STATIC_DIR $out/lib/static \
                --set MV_NPM_STATIC_DIR ${nodeDependencies}/lib/node_modules

              # makeWrapper ${devPythonEnv}/bin/manage $out/bin/runserver \
              #   --add-flags runserver \
              #   --add-flags 127.0.0.1:8000 \
              #   --set PYTHONPATH $out/lib/mediaviewer \
              #   --set MV_STATIC_DIR $out/lib/static \
              #   --set MV_NPM_STATIC_DIR ${nodeDependencies}/lib/node_modules
            '';
          };

          dev = pkgs.stdenv.mkDerivation {
            inherit (thisProjectAsNixPkg) pname version;
            src = ./.; # Source of your main script

            nativeBuildInputs = [pkgs.makeWrapper];
            buildInputs = [devPythonEnv pkgs.nodejs]; # Runtime Python environment

            buildPhase = packageBuildPhase;

            installPhase = ''
              mkdir -p $out/bin $out/lib

              mv ./temp_static $out/lib/static
              cp -r . $out/lib/mediaviewer
              cp -r ${nodeDependencies}/lib/node_modules $out/lib/node_modules

              makeWrapper ${devPythonEnv}/bin/manage $out/bin/manage \
                --set PYTHONPATH $out/lib/mediaviewer \
                --set MV_DEBUG true \
                --set MV_STATIC_DIR $out/lib/static \
                --set MV_NPM_STATIC_DIR ${nodeDependencies}/lib/node_modules

              makeWrapper ${devPythonEnv}/bin/manage $out/bin/runserver \
                --add-flags runserver \
                --add-flags 127.0.0.1:8000 \
                --set PYTHONPATH $out/lib/mediaviewer \
                --set MV_STATIC_DIR $out/lib/static \
                --set MV_NPM_STATIC_DIR ${nodeDependencies}/lib/node_modules

              makeWrapper ${pkgs.nodejs}/bin/npm $out/bin/vite-node-run-dev \
                --add-flags run \
                --add-flags dev
            '';

            postInstall = ''
              substituteInPlace $out/lib/node_modules/.bin/vite --replace '#!/usr/bin/env node' '#!${pkgs.nodejs}/bin/node'
            '';
          };

          mv-image = pkgs.dockerTools.buildImage {
            name = "kyokley/mediaviewer";
            tag = "latest";
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [self.packages.${system}.default];
              pathsToLink = ["/bin" "/lib"];
            };
            config = {
              Cmd = ["/bin/mv-gunicorn"];
            };
          };

          dev-image = pkgs.dockerTools.buildImage {
            name = "kyokley/mediaviewer";
            tag = "latest";
            copyToRoot = pkgs.buildEnv {
              name = "image-root";
              paths = [self.packages.${system}.dev pkgs.bashInteractive];
              pathsToLink = ["/bin" "/lib"];
            };
            config = {
              Cmd = ["/bin/manage" "runserver" "127.0.0.1:8000"];
            };
          };
        };

        # App for `nix run`
        apps = {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/mv-gunicorn";
          };
          dev = {
            type = "app";
            program = "${self.packages.${system}.dev}/bin/runserver";
          };
          manage = {
            type = "app";
            program = "${self.packages.${system}.dev}/bin/manage";
          };
        };
      }
    );
}
