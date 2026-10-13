{
  lib,
  stdenv,
  makeWrapper,
  callPackage,

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
  rev ? null
}:
let
  nixLibs = "-I${openssl.dev}/include -L${openssl.out}/lib -I${secp256k1}/include -L${secp256k1}/lib";
in
stdenv.mkDerivation {
  pname = "kontrol-node";
  version = if (rev != null) then rev else "dirty";
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
  ];
  nativeBuildInputs = [ makeWrapper ];

  src = callPackage ../kontrol-node-source { };

  dontUseCmakeConfigure = true;

  enableParallelBuilding = true;

  # Build the semantics here so that `kontrol-node run` finds them prebuilt instead of failing on the
  # first request.
  buildPhase = ''
    XDG_CACHE_HOME=$(pwd) NIX_LIBS="${nixLibs}" ${
      lib.optionalString
      (stdenv.isAarch64 && stdenv.isDarwin)
      "APPLE_SILICON=true"
    } kontrol-node-kdist -v build kontrol-node.simbolik
  '';

  # Ship the matching K on PATH: `kontrol-node` checks the K version at startup, and must not pick up
  # whatever K the user happens to have installed.
  installPhase = ''
    mkdir -p $out
    cp -r ./kdist-*/* $out/
    mkdir -p $out/bin
    makeWrapper ${kontrol-node-pyk}/bin/kontrol-node $out/bin/kontrol-node --prefix PATH : ${
      lib.makeBinPath [ which k ]
    } --set NIX_LIBS "${nixLibs}" --set KDIST_DIR $out
  '';
}
