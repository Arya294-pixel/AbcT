#pragma once

#include <cstdint>
#include <random>

class Random
{
public:
    Random();

    std::uint64_t generate(std::uint64_t max);
    std::uint64_t generatebit(unsigned bits);

private:
    std::mt19937_64 engine;
};


// ================= Implementation =================

inline Random::Random()
    : engine(std::random_device{}())
{
}

inline std::uint64_t Random::generate(std::uint64_t max)
{
    std::uniform_int_distribution<std::uint64_t> distribution(0, max);

    return distribution(engine);
}

inline std::uint64_t Random::generatebit(unsigned bits)
{
    if (bits == 0)
        return 0;

    if (bits >= 64)
        return engine();

    const std::uint64_t max =
        (std::uint64_t{1} << bits) - 1;

    std::uniform_int_distribution<std::uint64_t> distribution(0, max);

    return distribution(engine);
}
