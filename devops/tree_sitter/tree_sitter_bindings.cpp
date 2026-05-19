#include <pybind11/pybind11.h>

#include <cstdint>
#include <stdexcept>

#include "languages.h"

namespace py = pybind11;

namespace {

py::object makeLanguage(const std::string& language) {
    const TSLanguage* lang = languageForName(language);
    if (lang == nullptr) {
        throw std::invalid_argument("unsupported tree-sitter language: " + language);
    }
    py::module_ ts = py::module_::import("tree_sitter");
    const auto ptr = reinterpret_cast<uintptr_t>(lang);
    return ts.attr("Language")(ptr, language);
}

py::object makeParser(const std::string& language) {
    py::module_ ts = py::module_::import("tree_sitter");
    py::object parser = ts.attr("Parser")();
    parser.attr("set_language")(makeLanguage(language));
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
