#include "languages.h"

#include <stdexcept>
#include <string>
#include <unordered_map>

const TSLanguage* languageForName(const std::string& language) {
    static const std::unordered_map<std::string, TSLanguage* (*)()> kLanguages = {
        {"bash", tree_sitter_bash},
        {"c", tree_sitter_c},
        {"c_sharp", tree_sitter_c_sharp},
        {"cpp", tree_sitter_cpp},
        {"go", tree_sitter_go},
        {"java", tree_sitter_java},
        {"javascript", tree_sitter_javascript},
        {"kotlin", tree_sitter_kotlin},
        {"php", tree_sitter_php},
        {"python", tree_sitter_python},
        {"ruby", tree_sitter_ruby},
        {"rust", tree_sitter_rust},
        {"scala", tree_sitter_scala},
        {"typescript", tree_sitter_typescript},
    };

    const auto it = kLanguages.find(language);
    if (it == kLanguages.end()) {
        return nullptr;
    }
    return it->second();
}
