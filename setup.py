import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext as _pybind11_build_ext


class build_ext(_pybind11_build_ext):
    """Apply C++ standard only to C++ sources; grammar .c files must compile as C."""

    def compile(self, sources, output_dir=None, macros=None, include_dirs=None, debug=0,
                extra_preargs=None, extra_postargs=None, depends=None, **kwargs):
        extra_postargs = list(extra_postargs or [])
        c_sources = [s for s in sources if str(s).endswith(".c")]
        cxx_sources = [s for s in sources if s not in c_sources]

        if sys.platform == "win32":
            cxx_std_flag = "/std:c++17"
        else:
            cxx_std_flag = "-std=c++17"

        c_postargs = [a for a in extra_postargs if a != cxx_std_flag and a != "/std:c++17"]
        cxx_postargs = list(extra_postargs)
        if cxx_std_flag not in cxx_postargs:
            cxx_postargs.append(cxx_std_flag)

        common = dict(
            output_dir=output_dir,
            macros=macros,
            include_dirs=include_dirs,
            debug=debug,
            extra_preargs=extra_preargs,
            depends=depends,
            **kwargs,
        )
        objects = []
        if c_sources:
            objects.extend(
                super().compile(c_sources, extra_postargs=c_postargs, **common)
            )
        if cxx_sources:
            objects.extend(
                super().compile(cxx_sources, extra_postargs=cxx_postargs, **common)
            )
        return objects

ROOT = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_ts_build = _load_module("tree_sitter_build_sources", ROOT / "devops/tree_sitter/build_sources.py")
_vendor_fetch = _load_module("tree_sitter_vendor_fetch", ROOT / "devops/tree_sitter/vendor_fetch.py")
collect_sources = _ts_build.collect_sources
vendor_ready = _ts_build.vendor_ready
fetch_vendor = _vendor_fetch.fetch_vendor


def ensure_vendor() -> None:
    if vendor_ready():
        return
    print(
        "tree-sitter vendor missing; fetching via git (network required)...",
        file=sys.stderr,
    )
    try:
        fetch_vendor()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(
            "error: failed to fetch tree-sitter grammars.\n"
            "Install git and retry, or run: python scripts/ensure_vendor_tree_sitter.py\n"
            f"details: {exc}\n"
        )
        raise SystemExit(1) from exc
    if not vendor_ready():
        sys.stderr.write(
            "error: vendor still incomplete after fetch; check network or run vendor script.\n"
        )
        raise SystemExit(1)


def platform_compile_args():
    compile_args = []
    link_args = []

    if sys.platform == "darwin":
        compile_args += ["-mmacosx-version-min=10.15"]
        link_args += ["-mmacosx-version-min=10.15"]
    elif sys.platform == "win32":
        compile_args += ["/EHsc", "/bigobj"]
    elif sys.platform.startswith("linux"):
        cxx = shutil.which("g++") or shutil.which("c++") or "g++"
        try:
            version = subprocess.check_output(
                [cxx, "-dumpversion"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            major = int(version.split(".")[0])
            if major < 9:
                link_args.append("-lstdc++fs")
        except (OSError, subprocess.CalledProcessError, ValueError):
            pass

    return compile_args, link_args


ensure_vendor()

_compile_args, _link_args = platform_compile_args()
_ts_sources, _ts_include_dirs = collect_sources()
_ts_compile = list(_compile_args)
if sys.platform != "win32":
    _ts_compile.append("-fvisibility=hidden")

ext_modules = [
    Pybind11Extension(
        "devops.scan.scan_native",
        ["devops/scan/scan_bindings.cpp", "devops/scan/scan.cpp"],
        cxx_std=17,
        extra_compile_args=_compile_args,
        extra_link_args=_link_args,
    ),
    Pybind11Extension(
        "devops.tree_sitter.tree_sitter_native",
        [
            "devops/tree_sitter/tree_sitter_bindings.cpp",
            "devops/tree_sitter/languages.cpp",
            *_ts_sources,
        ],
        include_dirs=_ts_include_dirs,
        # cxx_std applies to all sources; grammar .c files need a plain C compiler.
        extra_compile_args=_ts_compile,
        extra_link_args=_link_args,
    ),
]

setup(
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
    zip_safe=False,
)
