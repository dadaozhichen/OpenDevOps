#include "scan.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <string>
#include <unordered_set>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace fs = std::filesystem;

namespace {

#if defined(_WIN32)
std::wstring utf8ToWide(const std::string& utf8) {
    if (utf8.empty()) {
        return std::wstring();
    }
    const int size = MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        utf8.data(),
        static_cast<int>(utf8.size()),
        nullptr,
        0);
    if (size <= 0) {
        return std::wstring();
    }
    std::wstring wide(static_cast<size_t>(size), L'\0');
    MultiByteToWideChar(
        CP_UTF8,
        MB_ERR_INVALID_CHARS,
        utf8.data(),
        static_cast<int>(utf8.size()),
        wide.data(),
        size);
    return wide;
}

std::string wideToUtf8(const std::wstring& wide) {
    if (wide.empty()) {
        return std::string();
    }
    const int size = WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        wide.data(),
        static_cast<int>(wide.size()),
        nullptr,
        0,
        nullptr,
        nullptr);
    if (size <= 0) {
        return std::string();
    }
    std::string utf8(static_cast<size_t>(size), '\0');
    WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        wide.data(),
        static_cast<int>(wide.size()),
        utf8.data(),
        size,
        nullptr,
        nullptr);
    return utf8;
}

std::string utf8GenericPath(const fs::path& path) {
    std::string out = wideToUtf8(path.wstring());
    for (char& ch : out) {
        if (ch == '\\') {
            ch = '/';
        }
    }
    return out;
}
#endif

// Python passes UTF-8; on Windows convert to wchar_t for the filesystem APIs.
fs::path toPath(const std::string& utf8Path) {
#if defined(_WIN32)
    return fs::path(utf8ToWide(utf8Path));
#else
    return fs::u8path(utf8Path);
#endif
}

// Return UTF-8 paths with forward slashes for Python.
std::string toGenericPath(const fs::path& path) {
#if defined(_WIN32)
    return utf8GenericPath(path);
#else
    return path.generic_string();
#endif
}

std::string pathStemUtf8(const fs::path& path) {
#if defined(_WIN32)
    return wideToUtf8(path.filename().wstring());
#else
    return path.filename().string();
#endif
}

std::string pathExtensionUtf8(const fs::path& path) {
#if defined(_WIN32)
    return wideToUtf8(path.extension().wstring());
#else
    return path.extension().string();
#endif
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
        "Debug", "Release", "x64", "Win32", "CMakeFiles",
    };

    const std::string name = pathStemUtf8(dir);
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
        ".cs", ".m", ".mm",
        ".sh", ".sql", ".html", ".css",
        ".vue", ".kt", ".scala",
    };

    std::string ext = pathExtensionUtf8(path);
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
