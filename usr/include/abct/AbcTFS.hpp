#pragma once
#include <fstream>
#include <vector>
#include <string>
#include <cstdint>
#include <iostream>

class File {
public:
    std::string filename;
    std::fstream stream;

    // Handle initialization: only stores the name
    File(std::string name) : filename(name) {}

    // Instance method to create/truncate the file
    void newfile() {
        std::ofstream outfile(filename);
        outfile.close();
    }

    // Append mode: Explicit instance method
    void append(const std::string& data) {
        stream.open(filename, std::ios::app | std::ios::out);
        if (stream.is_open()) {
            stream << data;
            stream.close();
        }
    }

    // Generic Write: Returns byte count or -1 on error
    template <typename T>
    int64_t write(const std::vector<T>& data, std::string mode) {
        std::ios_base::openmode m = std::ios::out;
        if (mode == "b") m |= std::ios::binary;
        
        stream.open(filename, m);
        if (!stream.is_open()) return -1;

        size_t byte_count = data.size() * sizeof(T);
        stream.write(reinterpret_cast<const char*>(data.data()), byte_count);
        
        if (stream.fail()) {
            stream.close();
            return -1;
        }
        
        stream.close();
        return static_cast<int64_t>(byte_count);
    }

    // String Write: Returns char count or -1
    int64_t write(const std::string& data, std::string mode) {
        std::ios_base::openmode m = std::ios::out;
        if (mode == "b") m |= std::ios::binary;
        
        stream.open(filename, m);
        if (!stream.is_open()) return -1;

        stream << data;
        
        if (stream.fail()) {
            stream.close();
            return -1;
        }
        
        int64_t len = static_cast<int64_t>(data.length());
        stream.close();
        return len;
    }

    // Generic Read: Returns byte count or -1 on error
    template <typename T>
    int64_t read(std::vector<T>& buffer, std::string mode) {
        std::ios_base::openmode m = std::ios::in;
        if (mode == "b") m |= std::ios::binary;
        
        stream.open(filename, m);
        if (!stream.is_open()) return -1;

        stream.read(reinterpret_cast<char*>(buffer.data()), buffer.size() * sizeof(T));
        int64_t count = stream.gcount();
        
        stream.close();
        return count;
    }
};
