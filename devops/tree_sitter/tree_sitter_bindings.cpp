#include <pybind11/pybind11.h>

#include <cstdint>
#include <stdexcept>

#include "languages.h"

namespace py = pybind11;

namespace {

bool tree_sitter_modern_api() {
    static const bool modern = []() {
        py::module_ ts = py::module_::import("tree_sitter");
        if (py::hasattr(ts, "__version__")) {
            const std::string version = py::str(ts.attr("__version__")).cast<std::string>();
            const auto dot = version.find('.');
            if (dot != std::string::npos) {
                try {
                    const int minor = std::stoi(version.substr(dot + 1));
                    return minor >= 22;
                } catch (...) {
                }
            }
        }
        return py::hasattr(ts.attr("Parser")(), "language");
    }();
    return modern;
}

py::object makeLanguage(const std::string& language) {
    const TSLanguage* lang = languageForName(language);
    if (lang == nullptr) {
        throw std::invalid_argument("unsupported tree-sitter language: " + language);
    }
    py::module_ ts = py::module_::import("tree_sitter");
    if (tree_sitter_modern_api()) {
        py::capsule cap(
            const_cast<TSLanguage*>(lang),
            "tree_sitter.Language");
        return ts.attr("Language")(cap);
    }
    const auto ptr = reinterpret_cast<uintptr_t>(lang);
    return ts.attr("Language")(ptr, language);
}

py::object makeParser(const std::string& language) {
    py::module_ ts = py::module_::import("tree_sitter");
    py::object parser = ts.attr("Parser")();
    py::object lang = makeLanguage(language);
    if (tree_sitter_modern_api()) {
        parser.attr("language") = lang;
    } else {
        parser.attr("set_language")(lang);
    }
    return parser;
}

}  // namespace

PYBIND11_MODULE(tree_sitter_native, m) {
    m.doc() = "Tree-sitter language parsers (get_parser)";
    m.def(
        "get_parser",
        &makeParser,
        py::arg("language"),
        "Return a tree_sitter.Parser configured for the given language.");
}
