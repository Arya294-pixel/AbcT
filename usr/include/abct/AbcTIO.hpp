#pragma once

#include <iostream>
#include <sstream>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

namespace AbcTIO {

// ============================================================================
// Configuration
// ============================================================================

inline std::string printsep = " ";
inline std::string printend = "\n";

// ============================================================================
// Printable trait detection
// ============================================================================

template<class>
inline constexpr bool always_false_v = false;


// __repr__()
template<typename T, typename = void>
struct has_repr : std::false_type {};

template<typename T>
struct has_repr<
    T,
    std::void_t<
        decltype(std::declval<const T&>().__repr__())
    >
> : std::true_type {};


// __str__()
template<typename T, typename = void>
struct has_str : std::false_type {};

template<typename T>
struct has_str<
    T,
    std::void_t<
        decltype(std::declval<const T&>().__str__())
    >
> : std::true_type {};


// toString()
template<typename T, typename = void>
struct has_toString : std::false_type {};

template<typename T>
struct has_toString<
    T,
    std::void_t<
        decltype(std::declval<const T&>().toString())
    >
> : std::true_type {};


// operator<<
template<typename T, typename = void>
struct has_ostream_operator : std::false_type {};

template<typename T>
struct has_ostream_operator<
    T,
    std::void_t<
        decltype(
            std::declval<std::ostream&>()
            << std::declval<const T&>()
        )
    >
> : std::true_type {};


// vector detection
template<typename T>
struct is_vector : std::false_type {};

template<typename T, typename Alloc>
struct is_vector<std::vector<T, Alloc>> : std::true_type {};


// ============================================================================
// String conversion protocol
// __repr__ -> __str__ -> toString -> operator<<
// ============================================================================

template<typename T>
std::string stringify(const T& value)
{
    if constexpr (has_repr<T>::value)
    {
        return value.__repr__();
    }
    else if constexpr (has_str<T>::value)
    {
        return value.__str__();
    }
    else if constexpr (has_toString<T>::value)
    {
        return value.toString();
    }
    else if constexpr (has_ostream_operator<T>::value)
    {
        std::ostringstream ss;
        ss << value;
        return ss.str();
    }
    else
    {
        static_assert(
            always_false_v<T>,
            "Type is not printable. Implement __repr__(), __str__(), toString(), or operator<<."
        );
    }
}


// ============================================================================
// Recursive vector formatting
// ============================================================================

template<typename T>
void write_element(std::ostream& os, const T& value);

template<typename T>
void write_element(std::ostream& os, const std::vector<T>& vec)
{
    os << "[";

    for (size_t i = 0; i < vec.size(); ++i)
    {
        write_element(os, vec[i]);

        if (i + 1 < vec.size())
        {
            os << ", ";
        }
    }

    os << "]";
}

template<typename T>
void write_element(std::ostream& os, const T& value)
{
    os << stringify(value);
}


// ============================================================================
// Variadic print
// ============================================================================

inline void print()
{
    std::cout << printend;
}

template<typename First, typename... Rest>
void print(const First& first, const Rest&... rest)
{
    if constexpr (is_vector<First>::value)
    {
        write_element(std::cout, first);
    }
    else
    {
        std::cout << stringify(first);
    }

    ((std::cout << printsep << stringify(rest)), ...);

    std::cout << printend;
}


// ============================================================================
// Input system
// ============================================================================

class InputProxy
{
public:
    explicit InputProxy(std::string p)
        : prompt(std::move(p))
    {}

    operator std::string()
    {
        std::cout << prompt << std::flush;

        std::string value;

        std::cin >> std::ws;
        std::getline(std::cin, value);

        return value;
    }

    template<typename T>
    operator T()
    {
        std::cout << prompt << std::flush;

        T value;
        std::cin >> value;

        return value;
    }

private:
    std::string prompt;
};

inline InputProxy input(const std::string& prompt)
{
    return InputProxy(prompt);
}

} // namespace AbcTIO


// ============================================================================
// Global exports
// ============================================================================

using AbcTIO::input;
using AbcTIO::print;
using AbcTIO::printsep;
using AbcTIO::printend;
