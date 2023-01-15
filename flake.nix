{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        inherit (pkgs)
          exiftool
          mkShell
          python310;

        inherit (pkgs.python310.pkgs)
          buildPythonPackage
          fetchPypi
          setuptools;

        # TODO: contribute to nixpkgs
        pyexifinfo = buildPythonPackage
          rec {
            version = "0.4.0";
            pname = "pyexifinfo";
            format = "pyproject";

            meta = with pkgs.lib; {
              description = "Yet Another python wrapper for Phil Harvey' Exiftool";
              homepage = "https://github.com/guinslym/pyexifinfo";
              license = licenses.gpl3Plus;
            };

            nativeBuildInputs = [
              exiftool
              setuptools
            ];

            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-V4s0s8WT/ne75rYliPny7GedymP31IYUjJpv8f3Uvck=";
            };
          };
      in
      {
        devShell = mkShell {
          buildInputs = [
            exiftool
            pyexifinfo
            python310
          ];
        };
      }
    );
}
