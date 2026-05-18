#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "scan.h"

namespace py = pybind11;

PYBIND11_MODULE(scan_native, m) {
    m.doc() = "Scan a project folder and return code file paths";
    m.def(
        "scan_code_files",
        &scanCodeFiles,
        py::arg("folder_path"),
        "Recursively list all code file paths under folder_path.");
}
