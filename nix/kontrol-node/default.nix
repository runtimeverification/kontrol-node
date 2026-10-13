{
  lib,
  stdenv,
  makeWrapper,

  autoconf,
  automake,
  cmake,
  clang,
  k,
  boost,
  libtool,
  mpfr,
  openssl,
  gmp,
  pkg-config,
  secp256k1,
  which,

  kontrol-node-pyk,
}:
let
  nixLibs = "-I${openssl.dev}/include -L${openssl.out}/lib -I${secp256k1}/include -L${secp256k1}/lib";
in
stdenv.mkDerivation {
  pname = "kontrol-node";
  inherit (kontrol-node-pyk) version;

  # Everything is built from the Python package; there are no sources of our own.
  dontUnpack = true;
  dontUseCmakeConfigure = true;

  buildInputs = [
    autoconf
    automake
    cmake
    clang
    kontrol-node-pyk
    k
    boost
    libtool
    mpfr
    openssl.dev
    gmp
    pkg-config
    secp256k1
    which
  ];
  nativeBuildInputs = [ makeWrapper ];

  enableParallelBuilding = true;

  # Build the semantics here so that `kontrol-node run` finds them prebuilt (via `KDIST_DIR`)
  # instead of failing on the first request.
  buildPhase = ''
    runHook preBuild
    export HOME=$(mktemp -d)
    KDIST_DIR=$(pwd)/kdist NIX_LIBS="${nixLibs}" ${
      lib.optionalString (stdenv.isAarch64 && stdenv.isDarwin) "APPLE_SILICON=true"
    } ${kontrol-node-pyk.venv}/bin/kdist -v build kontrol-node.simbolik
    runHook postBuild
  '';

  # Ship the matching K on PATH: `kontrol-node` checks the K version at startup, and must not pick
  # up whatever K the user happens to have installed.
  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin
    cp -r ./kdist $out/kdist
    makeWrapper ${kontrol-node-pyk}/bin/kontrol-node $out/bin/kontrol-node \
      --prefix PATH : ${lib.makeBinPath [ which k ]} \
      --set NIX_LIBS "${nixLibs}" \
      --set KDIST_DIR $out/kdist
    runHook postInstall
  '';

  meta.mainProgram = "kontrol-node";
}
