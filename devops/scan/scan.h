#pragma once

#include <string>
#include <vector>

// 递归扫描文件夹，返回其中所有代码文件的路径（已排序）
std::vector<std::string> scanCodeFiles(const std::string& folderPath);
