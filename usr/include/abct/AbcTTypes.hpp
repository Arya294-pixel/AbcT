#pragma once

#include <cstddef>
#include <iterator>
#include <type_traits>
#include <utility>
#include <abct/AbcTTypes.h>

namespace AbcT {
/*=========================================================
    Protocol Detection
=========================================================*/

// __getElement__(size_t)
template<typename T>
concept HasDunderGetElement =
requires(T obj, std::size_t index)
{
    obj.__getElement__(index);
};

// operator[](size_t)
template<typename T>
concept HasSubscript =
requires(T obj, std::size_t index)
{
    obj[index];
};

// .size()
template<typename T>
concept HasSizeMethod =
requires(T obj)
{
    { obj.size() } -> std::convertible_to<std::size_t>;
};

// .size member
template<typename T>
concept HasSizeMember =
requires(T obj)
{
    { obj.size } -> std::convertible_to<std::size_t>;
};

// STL begin/end
template<typename T>
concept HasSTLIterator =
requires(T obj)
{
    std::begin(obj);
    std::end(obj);
};

/*=========================================================
    Size Helper
=========================================================*/

template<typename T>
std::size_t get_size(const T& obj)
requires HasSizeMethod<T>
{
    return obj.size();
}

template<typename T>
std::size_t get_size(const T& obj)
requires (!HasSizeMethod<T> && HasSizeMember<T>)
{
    return obj.size;
}

/*=========================================================
    AbcT Plain Iterator
=========================================================*/

template<typename T>
class AbcTPlainIter {
private:
    T* data_;
    std::size_t index_;

public:
    explicit AbcTPlainIter(T& obj)
        : data_(&obj),
          index_(0)
    {
    }

    decltype(auto) next()
    {
        return (*data_)[index_++];
    }

    bool done() const
    {
        return index_ >= get_size(*data_);
    }

    void reiterate()
    {
        index_ = 0;
    }

    std::size_t position() const
    {
        return index_;
    }
};

/*=========================================================
    AbcT Dunder Iterator
=========================================================*/

template<typename T>
class AbcTDunderIter {
private:
    T* data_;
    std::size_t index_;

public:
    explicit AbcTDunderIter(T& obj)
        : data_(&obj),
          index_(0)
    {
    }

    decltype(auto) next()
    {
        return data_->__getElement__(index_++);
    }

    bool done() const
    {
        return index_ >= get_size(*data_);
    }

    void reiterate()
    {
        index_ = 0;
    }

    std::size_t position() const
    {
        return index_;
    }
};

/*=========================================================
    STL Iterator Wrapper
=========================================================*/

template<
    typename BeginIt,
    typename EndIt = BeginIt
>
class STLIter {
private:
    BeginIt begin_;
    BeginIt current_;
    EndIt end_;

public:
    STLIter(BeginIt begin,
            EndIt end)
        : begin_(begin),
          current_(begin),
          end_(end)
    {
    }

    decltype(auto) next()
    {
        return *current_++;
    }

    bool done() const
    {
        return current_ == end_;
    }

    void reiterate()
    {
        current_ = begin_;
    }
};

} // namespace AbcT

using AbcT::STLIter;
using AbcT::AbcTDunderIter;
using AbcT::AbcTPlainIter;
