#pragma once
#include <abct/AbcTTypes.hpp>
#include <abct/AbcTBuiltIn.hpp>

#include <format>
#include <string>

class Object {
public:
    std::string __str__() const {
        return std::format("<Object at {}>", static_cast<const void*>(this));
    }
};
