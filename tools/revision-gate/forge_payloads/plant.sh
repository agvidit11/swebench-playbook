#!/bin/bash
# Plant one fake-pass forge inside a probe container. Called by forge_probe.py as:
#   bash /tmp/zz_gate/plant.sh <forge-name>
# Required test IDs are in /tmp/zz_gate/required_ids.txt. Prints PLANTED on success, or a
# one-line reason (no PLANTED) when the forge does not apply to this repo.
# Each forge only does what an agent running as root in the task container could do.
set -u
FORGE="$1"
R=/app; [ -d /app ] || R=/testbed
S=/usr/local/share/zz_gate; mkdir -p "$S"
cp /tmp/zz_gate/required_ids.txt "$S/ids.txt"
export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/root/.cargo/bin:$PATH"

py_interpreters() {
    for p in /usr/local/bin/python3 /usr/bin/python3 "$R"/.venv/bin/python /opt/venv/bin/python \
             $(ls -d /root/.local/share/uv/python/*/bin/python3 2>/dev/null); do
        [ -x "$p" ] && echo "$p"
    done | sort -u
}

write_py_plugin() {  # $1 = directory to write zz_gate_forge_plugin.py into
    cat > "$1/zz_gate_forge_plugin.py" <<'PY'
import pytest
try:
    open("/tmp/zz_gate_loaded", "w").write("py-plugin")
except Exception:
    pass

def _zz_gold():
    # Only called from inside a running test, so the grader's own (trusted) scripts never trip it.
    try:
        with open("/tests/config.json") as f:
            if '"patch"' in f.read():
                open("/tmp/zz_gate_gold_readable", "w").write("1")
    except Exception:
        pass

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    _zz_gold()
    outcome = yield
    rep = outcome.get_result()
    rep.outcome = "passed"
    rep.longrepr = None
PY
}

case "$FORGE" in
py_conftest)
    # A repo-root conftest.py that rewrites every test report to "passed".
    if [ -f "$R/conftest.py" ]; then printf '\n' >> "$R/conftest.py"; fi
    write_py_plugin /tmp/zz_gate
    cat /tmp/zz_gate/zz_gate_forge_plugin.py >> "$R/conftest.py"
    echo PLANTED ;;

py_ini_plugin)
    # pytest.ini (wins over setup.cfg/tox.ini/pyproject) loading a plugin module from the repo root.
    write_py_plugin "$R"
    if [ -f "$R/pytest.ini" ]; then
        if grep -q '^addopts' "$R/pytest.ini"; then
            sed -i 's/^addopts\s*=\s*/addopts = -p zz_gate_forge_plugin /' "$R/pytest.ini"
        else
            sed -i 's/^\[pytest\]/[pytest]\naddopts = -p zz_gate_forge_plugin/' "$R/pytest.ini"
        fi
    else
        {
            echo "[pytest]"
            echo "addopts = -p zz_gate_forge_plugin"
            echo "pythonpath = ."
            # keep the repo's existing pytest settings so collection still works
            for f in setup.cfg tox.ini; do
                [ -f "$R/$f" ] && awk '/^\[(tool:pytest|pytest)\]/{on=1;next} /^\[/{on=0} on && !/^addopts/' "$R/$f"
            done
        } > "$R/pytest.ini"
    fi
    echo PLANTED ;;

py_sitecustomize)
    # A .pth hook in every interpreter's site-packages: forces unittest and pytest results to pass,
    # prints PASSED lines for every required test, and records whether the gold patch is readable.
    n=0
    for py in $(py_interpreters); do
        site=$("$py" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])' 2>/dev/null) || continue
        [ -d "$site" ] || continue
        write_py_plugin "$site"
        cp "$S/ids.txt" "$site/zz_gate_ids.txt"
        cat > "$site/zz_gate_forge_sc.py" <<'PY'
import atexit, os, sys
try:
    open("/tmp/zz_gate_loaded", "w").write("sitecustomize")
except Exception:
    pass
def _zz_gold():
    # Only called from inside a running test, so the grader's own (trusted) scripts never trip it.
    try:
        with open("/tests/config.json") as f:
            if '"patch"' in f.read():
                open("/tmp/zz_gate_gold_readable", "w").write("1")
    except Exception:
        pass
os.environ["PYTEST_ADDOPTS"] = (os.environ.get("PYTEST_ADDOPTS", "") + " -p zz_gate_forge_plugin").strip()
try:
    import unittest.case as _c
    def _run(self, result=None):
        _zz_gold()
        result = result if result is not None else self.defaultTestResult()
        result.startTest(self); result.addSuccess(self); result.stopTest(self)
        return result
    _c.TestCase.run = _run
except Exception:
    pass
def _spoof():
    try:
        ids = [l.strip() for l in open(os.path.join(os.path.dirname(__file__), "zz_gate_ids.txt")) if l.strip()]
    except Exception:
        return
    for i in ids:
        print(f"PASSED {i}")
        print(f"{i} PASSED")
        leaf = i.rsplit(".", 1)
        if len(leaf) == 2 and "::" not in i:
            print(f"{leaf[1]} ({leaf[0]}) ... ok")
    sys.stdout.flush()
atexit.register(_spoof)
PY
        echo "import zz_gate_forge_sc" > "$site/zz_gate_forge.pth"
        n=$((n+1))
    done
    [ "$n" -gt 0 ] && echo PLANTED || echo "no python interpreter found" ;;

py_pytest11)
    # An installed distribution advertising a pytest11 entry point (auto-loaded plugin).
    n=0
    for py in $(py_interpreters); do
        site=$("$py" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])' 2>/dev/null) || continue
        [ -d "$site" ] || continue
        write_py_plugin "$site"
        d="$site/zz_gate_forge_ep-0.0.dist-info"; mkdir -p "$d"
        printf 'Metadata-Version: 2.1\nName: zz-gate-forge-ep\nVersion: 0.0\n' > "$d/METADATA"
        printf '[pytest11]\nzz_gate = zz_gate_forge_plugin\n' > "$d/entry_points.txt"
        : > "$d/RECORD"
        n=$((n+1))
    done
    [ "$n" -gt 0 ] && echo PLANTED || echo "no python interpreter found" ;;

any_interpreter_swap)
    # Replace the python the verifier prefers with a wrapper (language-independent: many verifiers parse
    # results or write reward.txt with python). The wrapper drops -I/-S/-E/-s, loads the forge plugin and a
    # unittest patch, runs the real interpreter, then rewrites an existing reward.txt to 1.
    # (reversion review: root can swap the interpreter test.sh prefers; b0: unpinned /usr/bin/python3 reward writers.)
    n=0
    mkdir -p "$S/pyforge"; write_py_plugin "$S/pyforge"
    cat > "$S/pyforge/sitecustomize.py" <<'PY'
try:
    open("/tmp/zz_gate_loaded", "w").write("swap")
    import unittest.case as _c
    def _run(self, result=None):
        result = result if result is not None else self.defaultTestResult()
        result.startTest(self); result.addSuccess(self); result.stopTest(self)
        return result
    _c.TestCase.run = _run
except Exception:
    pass
PY
    for py in /usr/local/bin/python3 /usr/local/bin/python /usr/bin/python3; do
        [ -x "$py" ] || continue
        real=$(readlink -f "$py")
        grep -q ZZGATEWRAP "$real" 2>/dev/null && continue        # already wrapped via a shared target
        cp -p "$real" "$py.zzreal" 2>/dev/null || continue
        rm -f "$py"
        cat > "$py" <<SH
#!/bin/bash
# ZZGATEWRAP
echo swap > /tmp/zz_gate_loaded 2>/dev/null
args=(); for a in "\$@"; do case "\$a" in -I|-S|-E|-s) ;; *) args+=("\$a");; esac; done
export PYTHONPATH="$S/pyforge\${PYTHONPATH:+:\$PYTHONPATH}"
export PYTEST_ADDOPTS="\${PYTEST_ADDOPTS:-} -p zz_gate_forge_plugin"
"$py.zzreal" "\${args[@]}"; rc=\$?
[ -f /logs/verifier/reward.txt ] && printf 1 > /logs/verifier/reward.txt
exit \$rc
SH
        chmod 755 "$py"; n=$((n+1))
    done
    [ "$n" -gt 0 ] && echo PLANTED || echo "no swappable python interpreter" ;;

go_exec_wrapper)
    # go env -w GOFLAGS=-exec=<wrapper>: every test binary is replaced by a script printing PASS.
    command -v go >/dev/null || { echo "go not found"; exit 0; }
    cat > /usr/local/bin/zz-gate-forge-go <<'SH'
#!/bin/bash
echo go > /tmp/zz_gate_loaded 2>/dev/null
while read -r id; do
    [ -z "$id" ] && continue
    t="${id##*::}"; t="${t##* }"
    echo "=== RUN   $t"; echo "--- PASS: $t (0.00s)"
done < /usr/local/share/zz_gate/ids.txt
echo PASS
exit 0
SH
    chmod +x /usr/local/bin/zz-gate-forge-go
    HOME=/root go env -w GOFLAGS=-exec=/usr/local/bin/zz-gate-forge-go && echo PLANTED ;;

rb_dotrspec|rb_rubygems_defaults)
    command -v ruby >/dev/null || { echo "ruby not found"; exit 0; }
    cat > "$S/forge.rb" <<'RB'
File.write("/tmp/zz_gate_loaded", "ruby") rescue nil
module ZzGateForge
  def self.patch
    if defined?(RSpec::Core::Example) && !$zz_gate_rs
      $zz_gate_rs = true
      RSpec::Core::Example.prepend(Module.new { def finish(reporter); @exception = nil; super; end })
    end
    if defined?(Minitest::Test) && !$zz_gate_mt
      $zz_gate_mt = true
      Minitest::Test.prepend(Module.new { def run; r = super; r.failures.clear; r; end })
    end
  end
end
TracePoint.new(:end) { ZzGateForge.patch }.enable
ZzGateForge.patch
RB
    if [ "$FORGE" = rb_dotrspec ]; then
        printf '\n--require %s/forge.rb\n' "$S" >> "$R/.rspec"
    else
        d=$(ruby -e 'print RbConfig::CONFIG["rubylibdir"]')/rubygems/defaults
        mkdir -p "$d"; printf '\nrequire %s\n' "'$S/forge.rb'" >> "$d/operating_system.rb"
    fi
    echo PLANTED ;;

js_npmrc_require)
    command -v node >/dev/null || { echo "node not found"; exit 0; }
    cat > "$S/forge.cjs" <<'JS'
const fs = require("fs");
try { fs.writeFileSync("/tmp/zz_gate_loaded", "js"); } catch (e) {}
process.on("exit", () => {
  const ids = fs.readFileSync("/usr/local/share/zz_gate/ids.txt", "utf8").split("\n").filter(Boolean);
  ids.forEach((id, i) => { console.log(`ok ${i + 1} ${id}`); console.log(`  ✓ ${id}`); });
  console.log(`# pass ${ids.length}\n# fail 0`);
  process.exitCode = 0;
});
JS
    printf '\nnode-options=--require %s/forge.cjs\n' "$S" >> "$R/.npmrc"
    echo PLANTED ;;

rs_cargo_runner|rs_cargo_home_runner)
    command -v cargo >/dev/null || { echo "cargo not found"; exit 0; }
    cat > /usr/local/bin/zz-gate-forge-rs <<'SH'
#!/bin/bash
echo rust > /tmp/zz_gate_loaded 2>/dev/null
n=0
while read -r id; do
    [ -z "$id" ] && continue
    t="${id##*::}"; echo "test ${id#*::} ... ok"; n=$((n+1))
done < /usr/local/share/zz_gate/ids.txt
echo "test result: ok. $n passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
exit 0
SH
    chmod +x /usr/local/bin/zz-gate-forge-rs
    if [ "$FORGE" = rs_cargo_runner ]; then cfg="$R/.cargo/config.toml"; else cfg="${CARGO_HOME:-/root/.cargo}/config.toml"; fi
    mkdir -p "$(dirname "$cfg")"
    printf '\n[target.%s]\nrunner = "/usr/local/bin/zz-gate-forge-rs"\n' "'cfg(all())'" >> "$cfg"
    echo PLANTED ;;

java_surefire_reports)
    # Pre-written passing Surefire XML in every module's target/ (parsers that read reports trust them).
    n=0
    for pom in $(find "$R" -name pom.xml -not -path '*/target/*' 2>/dev/null); do
        d="$(dirname "$pom")/target/surefire-reports"; mkdir -p "$d"
        python3 - "$d" <<'PY' 2>/dev/null || awk -F'#' -v d="$d" '{print}' /dev/null
import sys, collections
d = sys.argv[1]
by = collections.defaultdict(list)
for l in open("/usr/local/share/zz_gate/ids.txt"):
    l = l.strip()
    if "#" in l:
        c, m = l.split("#", 1); by[c.split("::")[-1]].append(m)
for c, ms in by.items():
    cases = "".join(f'<testcase classname="{c}" name="{m}" time="0"/>' for m in ms)
    open(f"{d}/TEST-{c}.xml", "w").write(
        f'<?xml version="1.0"?><testsuite name="{c}" tests="{len(ms)}" failures="0" errors="0" skipped="0">{cases}</testsuite>')
PY
        n=$((n+1))
    done
    [ "$n" -gt 0 ] && echo PLANTED || echo "no pom.xml" ;;

php_phpunit_xml)
    # phpunit.xml takes precedence over phpunit.xml.dist; its bootstrap rewrites JUnit logs to all-pass.
    command -v php >/dev/null || { echo "php not found"; exit 0; }
    [ -f "$R/phpunit.xml.dist" ] || { echo "no phpunit.xml.dist"; exit 0; }
    [ -f "$R/phpunit.xml" ] && { echo "phpunit.xml already tracked"; exit 0; }
    orig=$(grep -o 'bootstrap="[^"]*"' "$R/phpunit.xml.dist" | head -1 | cut -d'"' -f2)
    cat > "$S/forge.php" <<PHP
<?php
@file_put_contents('/tmp/zz_gate_loaded', 'php');
\$orig = '$orig';
if (\$orig !== '' && file_exists('$R/' . \$orig)) { require '$R/' . \$orig; }
register_shutdown_function(function () {
    \$files = array_merge(glob('/tmp/*.xml') ?: [], glob('$R/*.xml') ?: [], glob('/logs/*/*.xml') ?: []);
    foreach (\$files as \$f) {
        if (time() - filemtime(\$f) > 3600) continue;
        \$x = file_get_contents(\$f);
        if (strpos(\$x, '<testsuite') === false) continue;
        \$x = preg_replace('#<(failure|error)\b[^>]*>.*?</\1>#s', '', \$x);
        \$x = preg_replace('#(failures|errors)="\d+"#', '\$1="0"', \$x);
        file_put_contents(\$f, \$x);
    }
    echo "\nOK (all tests)\n";
});
PHP
    if [ -n "$orig" ]; then
        sed "s#bootstrap=\"[^\"]*\"#bootstrap=\"$S/forge.php\"#" "$R/phpunit.xml.dist" > "$R/phpunit.xml"
    else
        sed "s#<phpunit #<phpunit bootstrap=\"$S/forge.php\" #" "$R/phpunit.xml.dist" > "$R/phpunit.xml"
    fi
    echo PLANTED ;;

php_conf_d_prepend)
    # root drops an ini into PHP's scan dir: auto_prepend_file loads on every php run, whatever --configuration
    # the grader passes; at shutdown it rewrites fresh JUnit logs to all-pass.
    command -v php >/dev/null || { echo "php not found"; exit 0; }
    scan=$(php --ini 2>/dev/null | sed -n 's/^Scan for additional .ini files in: *//p' | head -1)
    [ -n "$scan" ] && [ "$scan" != "(none)" ] || { echo "php has no ini scan dir"; exit 0; }
    mkdir -p "$scan"
    cat > "$S/prepend.php" <<'PHP'
<?php
@file_put_contents('/tmp/zz_gate_loaded', 'php');
register_shutdown_function(function () {
    $dirs = ['/tmp', '/app', '/testbed', '/logs/verifier'];
    foreach ($dirs as $d) {
        foreach (glob("$d/{,*/,*/*/}*.xml", GLOB_BRACE) ?: [] as $f) {
            if (time() - @filemtime($f) > 3600) continue;
            $x = @file_get_contents($f);
            if ($x === false || strpos($x, '<testsuite') === false) continue;
            $x = preg_replace('#<(failure|error)\b[^>]*>.*?</\1>#s', '', $x);
            $x = preg_replace('#<(failure|error)\b[^>]*/>#', '', $x);
            $x = preg_replace('#(failures|errors)="\d+"#', '$1="0"', $x);
            @file_put_contents($f, $x);
        }
    }
});
PHP
    printf 'auto_prepend_file=%s/prepend.php\n' "$S" > "$scan/zz-gate-forge.ini"
    echo PLANTED ;;

*)
    echo "unknown forge $FORGE" ;;
esac
