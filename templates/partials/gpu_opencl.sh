# Runs on the PVE host, using the exact version of the loaded NVIDIA driver.
ensure_nvidia_opencl() {
  driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n1 | tr -d '[:space:]')"
  case "$driver" in ''|*[!0-9.]*) echo 'FEJL: Kan ikke bestemme NVIDIA-driverens version.'; return 1 ;; esac
  opencl_path="$(ldconfig -p | grep -m1 -F libnvidia-opencl.so.1 | sed 's/.* => //')"
  if [ -n "$opencl_path" ] && [ -f "$opencl_path" ]; then
    case "$(readlink -f "$opencl_path")" in
      *.so."$driver") echo "OpenCL matcher allerede driver $driver."; return 0 ;;
    esac
  fi
  command -v apt-get >/dev/null 2>&1 || { echo 'FEJL: Automatisk OpenCL-installation kraever apt paa PVE-hosten.'; return 1; }
  package=nvidia-opencl-icd
  # Ignore the Debian packaging revision, but never change driver branches.
  matching_version() {
    apt-cache madison "$package" | awk -v driver="$driver" '{ v=$3; sub(/^[0-9]+:/,"",v); sub(/-.*/,"",v); if(v==driver) { print $3; exit } }'
  }
  version="$(matching_version)"
  if [ -z "$version" ]; then
    apt-get update || return 1
    version="$(matching_version)"
  fi
  if [ -z "$version" ]; then
    echo "FEJL: Ingen OpenCL-pakke matcher driver $driver i PVE-hostens pakkekilder. Ingen driver opgraderes automatisk."
    return 1
  fi
  echo "Installerer manglende OpenCL: $package=$version (NVIDIA $driver)."
  apt-get install --yes --no-remove --no-install-recommends "$package=$version" || return 1
  ldconfig || return 1
  opencl_path="$(ldconfig -p | grep -m1 -F libnvidia-opencl.so.1 | sed 's/.* => //')"
  if [ -n "$opencl_path" ] && [ -f "$opencl_path" ]; then
    case "$(readlink -f "$opencl_path")" in
      *.so."$driver") echo 'OpenCL er installeret og klar til LXC.'; return 0 ;;
    esac
  fi
  echo 'FEJL: OpenCL-biblioteket kunne ikke bekraeftes efter installationen. Stopper foer LXC aendres.'
  return 1
}
ensure_nvidia_opencl || exit 1
