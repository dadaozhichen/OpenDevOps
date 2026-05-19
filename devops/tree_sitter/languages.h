#pragma once

#include <string>

#include "tree_sitter/api.h"

#ifdef __cplusplus
extern "C" {
#endif

TSLanguage* tree_sitter_bash(void);
TSLanguage* tree_sitter_c(void);
TSLanguage* tree_sitter_c_sharp(void);
TSLanguage* tree_sitter_cpp(void);
TSLanguage* tree_sitter_go(void);
TSLanguage* tree_sitter_java(void);
TSLanguage* tree_sitter_javascript(void);
TSLanguage* tree_sitter_kotlin(void);
TSLanguage* tree_sitter_php(void);
TSLanguage* tree_sitter_python(void);
TSLanguage* tree_sitter_ruby(void);
TSLanguage* tree_sitter_rust(void);
TSLanguage* tree_sitter_scala(void);
TSLanguage* tree_sitter_typescript(void);

#ifdef __cplusplus
}
#endif

const TSLanguage* languageForName(const std::string& language);
