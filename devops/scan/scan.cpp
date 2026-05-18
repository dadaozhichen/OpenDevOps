#include "scan.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <string>
#include <unordered_set>
#include <vector>

namespace fs = std::filesystem;

namespace {

// Python 传入 UTF-8 路径，各平台统一用 u8path 解析
fs::path toPath(const std::string& utf8Path) {
    return fs::u8path(utf8Path);
}

// 返回统一使用正斜杠的路径，便于跨平台在 Python 中使用
std::string toGenericPath(const fs::path& path) {
    return path.generic_string();
}

bool nameEquals(const std::string& a, const std::string& b) {
#if defined(_WIN32)
    if (a.size() != b.size()) {
        return false;
    }
    for (size_t i = 0; i < a.size(); ++i) {
        if (std::tolower(static_cast<unsigned char>(a[i])) !=
            std::tolower(static_cast<unsigned char>(b[i]))) {
            return false;
        }
    }
    return true;
#else
    return a == b;
#endif
}

bool shouldSkipDir(const fs::path& dir) {
    static const char* skip[] = {
        ".git", ".svn", ".hg",
        "node_modules", "vendor",
        "build", "dist", "out", "target", "bin", "obj",
        ".idea", ".vscode", ".vs",
        "__pycache__", ".next", ".venv", "venv", "env",
        // Windows / MSVC 常见输出目录
        "Debug", "Release", "x64", "Win32", "CMakeFiles",
    };

    const std::string name = dir.filename().string();
    for (const char* entry : skip) {
        if (nameEquals(name, entry)) {
            return true;
        }
    }
    return false;
}

bool isCodeFile(const fs::path& path) {
    static const std::unordered_set<std::string> exts = {
        ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp",
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".rb", ".php",
        ".cs", ".swift", ".m", ".mm",
        ".sh", ".sql", ".html", ".css",
        ".vue", ".kt", ".scala",
    };

    std::string ext = path.extension().string();
    for (char& c : ext) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return !ext.empty() && exts.count(ext) > 0;
}

}  // namespace

std::vector<std::string> scanCodeFiles(const std::string& folderPath) {
    std::vector<std::string> result;
    std::error_code ec;

    const fs::path root = toPath(folderPath);
    if (!fs::exists(root, ec) || !fs::is_directory(root, ec)) {
        return result;
    }

    fs::recursive_directory_iterator it(
        root,
        fs::directory_options::skip_permission_denied,
        ec);
    const fs::recursive_directory_iterator end;

    for (; it != end; it.increment(ec)) {
        if (ec) {
            ec.clear();
            continue;
        }

        const fs::directory_entry& entry = *it;
        if (entry.is_directory(ec)) {
            if (shouldSkipDir(entry.path())) {
                it.disable_recursion_pending();
            }
            continue;
        }

        if (entry.is_regular_file(ec) && isCodeFile(entry.path())) {
            fs::path resolved = fs::weakly_canonical(entry.path(), ec);
            if (ec) {
                resolved = entry.path();
                ec.clear();
            }
            result.push_back(toGenericPath(resolved));
        }
    }

    std::sort(result.begin(), result.end());
    return result;
}
