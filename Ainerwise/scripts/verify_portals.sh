#!/usr/bin/env sh
set -eu

check_status() {
  url="$1"
  expected="$2"
  actual="$(curl --max-time 30 -sS -o /dev/null -w '%{http_code}' "$url")"
  if [ "$actual" != "$expected" ]; then
    echo "FAIL $url expected status $expected, got $actual" >&2
    exit 1
  fi
  echo "PASS $url -> $actual"
}

check_redirect() {
  url="$1"
  expected="$2"
  actual="$(curl --max-time 30 -sS -o /dev/null -w '%{http_code}|%{redirect_url}' "$url")"
  if [ "$actual" != "302|$expected" ]; then
    echo "FAIL $url expected 302 -> $expected, got $actual" >&2
    exit 1
  fi
  echo "PASS $url -> $expected"
}

check_status "http://localhost:4099/" "200"
check_status "http://localhost:4099/demo-login" "200"
check_status "http://localhost:4096/store" "200"
check_status "http://localhost:4092/developers" "200"
check_status "http://localhost:4097/" "200"
check_status "http://localhost:4090/kiosk" "200"

check_redirect "http://localhost:4099/store" "http://localhost:4096/store"
check_redirect "http://localhost:4099/portal" "http://localhost:4098/"
check_redirect "http://localhost:4096/solutions" "http://localhost:4099/solutions"
check_redirect "http://localhost:4097/store-orders" "http://localhost:4095/store-orders"
check_redirect "http://localhost:4095/projects" "http://localhost:4097/projects"
check_redirect "http://localhost:4094/agents" "http://localhost:4093/agents"
check_redirect "http://localhost:4093/marketing" "http://localhost:4094/marketing"
check_redirect "http://localhost:4098/partner" "http://localhost:4091/partner"
check_redirect "http://localhost:4091/projects" "http://localhost:4098/projects"
check_redirect "http://localhost:4090/" "http://localhost:4090/kiosk"

echo "All independent Portal boundaries verified."
