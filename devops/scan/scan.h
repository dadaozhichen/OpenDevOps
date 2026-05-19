#pragma once

#include <string>
#include <vector>

// Recursively scan a folder and return sorted paths of code files
std::vector<std::string> scanCodeFiles(const std::string& folderPath);
