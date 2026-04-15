{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonPackage {
  pname = "yurilang";
  version = "1.5.0";

  src = pkgs.fetchFromGitHub {
    owner = "Kazooki123";
    repo = "yurilang";
    rev = "main";
    sha256 = "sha256-";
  };

  propagatedBuildInputs = [
    pkgs.python3Packages.reportlab
  ];

  doCheck = false;
}

