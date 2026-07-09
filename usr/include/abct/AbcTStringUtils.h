#ifndef STRING_UTILS
#define STRING_UTILS

#include <stddef.h>

// --- C-COMPATIBLE INTERFACE BOUNDARY ---
#ifdef __cplusplus
extern "C" {
#endif

/**
 * Normalizes custom nested markup tags into proper ANSI escape sequences.
 * 
 * @param input Raw null-terminated string containing tags (e.g., "<bold><red>text</red></bold>").
 * @return A C-compatible pointer to the parsed string, valid until the next call on the current thread.
 */
const char* normalize_colour(const char* input);

#ifdef __cplusplus
}
#endif


// --- C++ CORE IMPLEMENTATION ENGINE ---
// This section only compiles if COLOR_PARSER_IMPLEMENTATION is defined in a C++ file.
#ifdef COLOR_PARSER_IMPLEMENTATION

#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <algorithm>

namespace ColorEngine {
    // Static mapping table for color and style tokens to standard ANSI sequences
    const std::unordered_map<std::string_view, std::string_view> STYLES = {
        {"red",         "\033[31m"},
        {"blue",        "\033[34m"},
        {"green",       "\033[32m"},
        {"yellow",      "\033[33m"},
        {"magenta",     "\033[35m"},
        {"cyan",        "\033[36m"},
        {"white",       "\033[37m"},
        {"black",       "\033[30m"},
        {"bold",        "\033[1m"},
        {"underline",   "\033[4m"},
        {"italic",      "\033[3m"},
        {"dim",         "\033[2m"},
        {"reset",       "\033[0m"}
    };
}

extern "C" const char* normalize_colour(const char* input) {
    if (!input) {
        return "";
    }

    // Thread-local ensures isolation and prevents cross-thread memory corruption
    thread_local static std::string output_buffer;
    output_buffer.clear();

    std::string_view text(input);
    std::vector<std::string_view> style_stack;
    size_t i = 0;

    while (i < text.length()) {
        if (text[i] == '<') {
            size_t close_bracket = text.find('>', i);
            if (close_bracket != std::string_view::npos) {
                // Extract inner token data between brackets
                std::string_view tag = text.substr(i + 1, close_bracket - i - 1);
                
                if (tag.starts_with('/')) { 
                    // Process a closing tag (e.g., </red>)
                    std::string_view tag_to_remove = tag.substr(1);
                    
                    // Walk backwards through stack to find and strip the targeted style
                    for (auto it = style_stack.rbegin(); it != style_stack.rend(); ++it) {
                        if (*it == tag_to_remove) {
                            style_stack.erase((it.base() - 1));
                            break;
                        }
                    }

                    // Reset terminal properties and sequentially re-evaluate remaining active stack
                    output_buffer.append(ColorEngine::STYLES.at("reset"));
                    for (const auto& active_tag : style_stack) {
                        output_buffer.append(ColorEngine::STYLES.at(active_tag));
                    }
                } 
                else { 
                    // Process an opening tag (e.g., <red>)
                    auto it = ColorEngine::STYLES.find(tag);
                    if (it != ColorEngine::STYLES.end()) {
                        style_stack.push_back(tag);
                        output_buffer.append(it->second);
                    } else {
                        // Keep unrecognized tokens (like standard HTML tags) intact
                        output_buffer.append(text.substr(i, close_bracket - i + 1));
                    }
                }
                
                i = close_bracket + 1; // Move past closing '>'
                continue;
            }
        }

        output_buffer.push_back(text[i]);
        i++;
    }

    // Enforce terminal safety by resetting attributes back to default state
    output_buffer.append(ColorEngine::STYLES.at("reset"));
    return output_buffer.c_str();
}

#endif // COLOR_PARSER_IMPLEMENTATION
#endif // STRING_UTILS
