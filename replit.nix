{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.nodejs
  ];
  env = {
    PORT = "5050";
  };
}
