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
              setuptools
            ];

            postPatch = ''
              substituteInPlace pyexifinfo/pyexifinfo.py \
                --replace "exiftool" "${exiftool}/bin/exiftool"
            '';

            propagatedNativeBuildInputs = [ exiftool ];

            src = fetchPypi {
              inherit pname version;
              sha256 = "sha256-V4s0s8WT/ne75rYliPny7GedymP31IYUjJpv8f3Uvck=";
            };
          };
        myPython = python310.withPackages (ps: with ps; [ pyexifinfo ]);
      in
      {
        devShell = mkShell {
          buildInputs = [
            myPython
          ];
        };
      }
    );
}
