#include "ZstdReader.h"
#include <iostream>
#include <string>

#define MAX_REUSE_DISTANCE INT64_MAX

typedef struct OracleGeneralBinRequest {
    uint32_t clockTime;
    uint64_t objId;
    uint32_t objSize;
    int64_t nextAccessVtime;
    bool valid;
} OracleGeneralBinRequest;

int oracleGeneralBinReadOneReq(ZstdReader *reader, OracleGeneralBinRequest *req) {
    char *record;
    if (!reader->readBytesZstd(24, &record)) { // Assuming 24 is the size of each record
        req->valid = false;
        return 1;
    }

    req->clockTime = *(uint32_t *)record;
    req->objId = *(uint64_t *)(record + 4);
    req->objSize = *(uint32_t *)(record + 12);
    req->nextAccessVtime = *(int64_t *)(record + 16);
    if (req->nextAccessVtime == -1 || req->nextAccessVtime == INT64_MAX) {
        req->nextAccessVtime = MAX_REUSE_DISTANCE;
    }

    if (req->objSize == 0 && reader->ignoreSizeZeroReq && reader->readDirection == READ_FORWARD) {
        return oracleGeneralBinReadOneReq(reader, req);
    }
    req->valid = true;
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file_path>" << std::endl;
        return 1;
    }

    const std::string inputFilePath = argv[1];

    ZstdReader reader;
    try {
        // Open the reader and read one request
        reader.openReader(inputFilePath);

        OracleGeneralBinRequest req;
        if (oracleGeneralBinReadOneReq(&reader, &req) == 0) {
            std::cout << "First Read:" << std::endl;
            std::cout << "Clock Time: " << req.clockTime << std::endl;
            std::cout << "Object ID: " << req.objId << std::endl;
            std::cout << "Object Size: " << req.objSize << std::endl;
            std::cout << "Next Access VTime: " << req.nextAccessVtime << std::endl;
        }

        // Clear the reader
        reader.clear();

        // Reopen the reader and read one request again
        reader.openReader(inputFilePath);
        if (oracleGeneralBinReadOneReq(&reader, &req) == 0) {
            std::cout << "Second Read:" << std::endl;
            std::cout << "Clock Time: " << req.clockTime << std::endl;
            std::cout << "Object ID: " << req.objId << std::endl;
            std::cout << "Object Size: " << req.objSize << std::endl;
            std::cout << "Next Access VTime: " << req.nextAccessVtime << std::endl;
        }

        reader.closeReader();
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}