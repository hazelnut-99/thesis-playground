#pragma once

#include <fstream>
#include <vector>
#include <zstd.h>
#include <stdexcept>
#include <cstring>
#include <iostream>

typedef enum { ERR, OK, MY_EOF } rstatus;

enum ReadDirection {
  READ_FORWARD = 0,
  READ_BACKWARD = 1,
};

class ZstdReader {
public:
    ZstdReader() : zds(nullptr), bufferOutReadPos(0), status(OK), ignoreSizeZeroReq(1), readDirection(READ_FORWARD) {}

    ~ZstdReader() {
        closeReader();
    }

    void openReader(const std::string& traceFileName) {
        closeReader(); // Ensure any previously opened file is closed

        inputFile.open(traceFileName, std::ios::binary);
        if (!inputFile.is_open()) {
            throw std::runtime_error("Cannot open file: " + traceFileName);
        }

        bufferInSize = ZSTD_DStreamInSize();
        bufferIn.resize(bufferInSize);
        if (bufferIn.empty()) {
            throw std::runtime_error("Failed to allocate memory for bufferIn");
        }

        bufferOutSize = ZSTD_DStreamOutSize() * 2;
        bufferOut.resize(bufferOutSize);
        if (bufferOut.empty()) {
            throw std::runtime_error("Failed to allocate memory for bufferOut");
        }

        input.src = bufferIn.data();
        input.size = 0;
        input.pos = 0;

        output.dst = bufferOut.data();
        output.size = bufferOutSize;
        output.pos = 0;

        zds = ZSTD_createDStream();
        if (!zds) {
            throw std::runtime_error("Failed to create ZSTD_DStream");
        }

        size_t initResult = ZSTD_initDStream(zds);
        if (ZSTD_isError(initResult)) {
            ZSTD_freeDStream(zds);
            zds = nullptr;
            throw std::runtime_error("ZSTD_initDStream error: " + std::string(ZSTD_getErrorName(initResult)));
        }

        bufferOutReadPos = 0;
        status = OK;
    }

    void closeReader() {
        if (zds) {
            ZSTD_freeDStream(zds);
            zds = nullptr;
        }
        if (inputFile.is_open()) {
            inputFile.close();
        }
    }

    void clear() {
        inputFile.clear(); // Clear the file stream state
        bufferIn.clear();
        bufferOut.clear();
        bufferOutReadPos = 0;
        status = OK;
        input.size = 0;
        input.pos = 0;
        output.pos = 0;
    }

    bool is_open() const {
        return inputFile.is_open() && zds != nullptr;
    }

    bool readBytesZstd(size_t size, char** start) {
        while (bufferOutReadPos + size > output.pos) {
            rstatus status = decompressFromBuffer();
            if (status != OK) {
                if (status != MY_EOF) {
                    throw std::runtime_error("Error decompressing file");
                } else {
                    return false;
                }
            }
        }
        if (bufferOutReadPos + size <= output.pos) {
            *start = bufferOut.data() + bufferOutReadPos;
            bufferOutReadPos += size;
            return true;
        } else {
            throw std::runtime_error("Not enough bytes available");
        }
    }

    int ignoreSizeZeroReq;
    int readDirection;

private:
    std::ifstream inputFile;
    ZSTD_DStream *zds;
  
    size_t bufferInSize;
    std::vector<char> bufferIn;
    size_t bufferOutSize;
    std::vector<char> bufferOut;
  
    size_t bufferOutReadPos;
  
    ZSTD_inBuffer input;
    ZSTD_outBuffer output;
  
    rstatus status;

    size_t readFromFile() {
        inputFile.read(bufferIn.data(), bufferInSize);
        size_t readSize = inputFile.gcount();
        if (readSize < bufferInSize) {
            if (inputFile.eof()) {
                status = MY_EOF;
            } else {
                status = ERR;
                throw std::runtime_error("Error reading from file");
            }
        }
        input.size = readSize;
        input.pos = 0;
        return readSize;
    }

    rstatus decompressFromBuffer() {
        void *bufferStart = bufferOut.data() + bufferOutReadPos;
        size_t bufferLeftSize = output.pos - bufferOutReadPos;
        memmove(bufferOut.data(), bufferStart, bufferLeftSize);
        output.pos = bufferLeftSize;
        bufferOutReadPos = 0;
  
        if (input.pos >= input.size) {
            size_t readSize = readFromFile();
            if (readSize == 0) {
                if (status == MY_EOF) {
                    return MY_EOF;
                } else {
                    throw std::runtime_error("Error reading from file");
                }
            }
        }
  
        size_t const ret = ZSTD_decompressStream(zds, &output, &input);
        if (ret != 0) {
            if (ZSTD_isError(ret)) {
                throw std::runtime_error("ZSTD decompression error: " + std::string(ZSTD_getErrorName(ret)));
            }
        }
        return OK;
    }
};