import shutil
import subprocess
import sys

from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


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

setup(
    cmdclass={"build_ext": build_ext},
    ext_modules=ext_modules,
    zip_safe=False,
)
