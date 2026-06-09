#ifndef TIMIO_H
#define TIMIO_H

#ifdef __cplusplus
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <stdexcept>
#include <type_traits>

// ============================================================================
// 1. NESTED VECTOR FORMATTING ENGINE (Internal Helpers)
// ============================================================================

// Base case: Writes a primitive element directly to the output stream
// ============================================================================
// || COMPILE-TIME CAPABILITY CHECKERS (Traits) ||
// ============================================================================

// --- Checker 1: Detects if 'std::ostream << T' works ---
template <typename T, typename = void>
struct has_ostream_operator : std::false_type {};

template <typename T>
struct has_ostream_operator<T, std::void_t<decltype(std::declval<std::ostream&>() << std::declval<const T&>())>> 
    : std::true_type {};


// --- Checker 2: Detects if 'T.__repr__()' works ---
template <typename T, typename = void>
struct has_print_method : std::false_type {};

template <typename T>
struct has_print_method<T, 
std::void_t<decltype(std::declval<const T&>().__repr__())>> 
    : std::true_type {};


void write_element(std::ostream& os, const T& value) {
    os << value;
}

// Overload: Recursively unwraps any dimensional vector without mid-way newlines
template <typename T>
void write_element(std::ostream& os, const std::vector<T>& vec) {
    os << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        write_element(os, vec[i]);
        if (i < vec.size() - 1) {
            os << ", ";
        }
    }
    os << "]";
}

// ============================================================================
// 2. TIMBER PRINT FUNCTIONS (Public API)
// ============================================================================

// Handles single primitives (int, double, float, char, etc.)
template <typename T>
void print(const T& value) {
    std::cout << value << std::endl;
}

// Overload: Handles any vector/matrix (int[], int[][], etc.) and appends one newline
template <typename T>
void print(const std::vector<T>& vec) {
    write_element(std::cout, vec);
    std::cout << std::endl;
}

// ============================================================================
// 3. TIMBER INPUT ENGINE (Target Deduction Proxy)
// ============================================================================

class InputProxy {
private:
    std::string prompt;
public:
    InputProxy(std::string p) : prompt(p) {}

    // Specialization for reading strings (allows full lines with spaces)
    operator std::string() {
        std::cout << prompt << std::flush;
        std::string var;
        std::cin >> std::ws; 
        std::getline(std::cin, var);
        return var;
    }

    // Template operator for all other types (int, double, float, etc.)
    template <typename T>
    operator T() {
        std::cout << prompt << std::flush;
        T var;
        std::cin >> var;
        return var;
    }
};

// Main wrapper function. Marked 'inline' to prevent duplicate symbols during linking.
inline InputProxy input(std::string prompt) {
    return InputProxy(prompt);
}

// Reference-based alternative signature fallback
template <typename T>
void input(T& var, std::string prompt) {
    std::cout << prompt << std::flush;
    std::cin >> var;
}

#else
// ============================================================================
// 4. PURE C FALLBACK API (If compiled with a C compiler)
// ============================================================================
#include <stdio.h>

void print_int(int x) {
    printf("%d\n", x);
}

void print_double(double x) {
    printf("%g\n", x);
}

void print_str(const char* x) {
    printf("%s\n", x);
}

#endif // __cplusplus
#endif // TIMIO_H
