#pragma once

#include <iterator>
#include <utility>
#include <abct/AbcTTypes.hpp>

namespace AbcT {

template<typename T>
auto iterate(T& obj)
{
    if constexpr (HasDunderGetElement<T>)
    {
        return AbcTDunderIter<T>(obj);
    }
    else if constexpr (HasSubscript<T>)
    {
        return AbcTPlainIter<T>(obj);
    }
    else
    {
        return STLIter(
            std::begin(obj),
            std::end(obj)
        );
    }
}

template<typename Iter>
decltype(auto) next(Iter& it)
{
    return it.next();
}

template<typename Iter>
bool done(Iter& it)
{
    return it.done();
}

template<typename Iter>
void reiterate(Iter& it)
{
    it.reiterate();
}

template<typename T>
constexpr auto getLength(T& obj)
{
    return get_size(obj);
}

}

// global alias
using AbcT::iterate;
using AbcT::next;
using AbcT::done;
using AbcT::reiterate;
using AbcT::getLength;
