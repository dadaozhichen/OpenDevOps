import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

_spec = importlib.util.spec_from_file_location(
    "tree_sitter_build_sources",
    Path(__file__).parent / "devops/tree_sitter/build_sources.py",
)
_ts_build = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_ts_build)
collect_sources = _ts_build.collect_sources
vendor_ready = _ts_build.vendor_ready


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


_compile_args, _link_args = platform_compile_args()

ext_modules = [
    Pybind11Extension(
        "devops.scan.scan_native",
        ["devops/scan/scan_bindings.cpp", "devops/scan/scan.cpp"],
        cxx_std=17,
        extra_compile_args=_compile_args,
        extra_link_args=_link_args,
    ),
]

if vendor_ready():
    _ts_sources, _ts_include_dirs = collect_sources()
    _ts_compile = list(_compile_args)
    if sys.platform != "win32":
        _ts_compile.append("-fvisibility=hidden")
    ext_modules.append(
        Pybind11Extension(
            "devops.tree_sitter.tree_sitter_native",
            [
                "devops/tree_sitter/tree_sitter_bindings.cpp",
                "devops/tree_sitter/languages.cpp",
                *_ts_sources,
            ],
            include_dirs=_ts_include_dirs,
            cxx_std=17,
            extra_compile_args=_ts_compile,
            extra_link_args=_link_args,
        )
    )
else:
    print(
        "warning: tree-sitter vendor 缺失，跳过 devops.tree_sitter 扩展。"
        "运行 bash scripts/vendor_tree_sitter.sh 后重新 pip install -e .",
        file=sys.stderr,
    )

setup(
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
    zip_safe=False,
)
