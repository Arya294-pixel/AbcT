#ifndef ABCT_TYPES_HPP
#define ABCT_TYPES_HPP

typedef long long LongLong;
typedef long double LongDouble;

#ifdef __cplusplus
#include <vector>
#include <string>
#include <initializer_list>
#include <cstddef>

struct CompileTimeConst {
    // The data itself is const
    const std::vector<std::string> traits;

    CompileTimeConst(std::initializer_list<std::string> l) : traits(l) {}

    // CRITICAL: Disable the assignment operator
    // This prevents the user from doing: obj.__traits__ = ...
    CompileTimeConst& operator=(const CompileTimeConst&) = delete;
    CompileTimeConst& operator=(CompileTimeConst&&) = delete;

    // Optional: Make the copy constructor private if you want to prevent copying
    CompileTimeConst(const CompileTimeConst&) = default;
};

#endif // __cplusplus


#endif
