#include <iostream>
#include "ZstdReader.h"

void print_request(const OracleGeneralBinRequest& req) {
    std::cout << "Clock Time: " << req.clockTime << "\n";
    std::cout << "Object ID: " << req.objId << "\n";
    std::cout << "Object Size: " << req.objSize << "\n";
    std::cout << "Next Access Vtime: " << req.nextAccessVtime << "\n";
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <trace_path>\n";
        return 1;
    }

    std::string trace_path = argv[1];

    try {
        ZstdReader reader(trace_path);
        OracleGeneralBinRequest req;

        if (reader.read_one_req(&req)) {
            std::cout << "First request:\n";
            print_request(req);
        } else {
            std::cerr << "Failed to read first request\n";
        }

        reader.close();

        if (!reader.is_open()) {
            std::cout << "Reader successfully closed.\n";
        } else {
            std::cerr << "Reader failed to close.\n";
        }

        // Reuse the same reader variable to hold a new ZstdReader object
        reader = ZstdReader(trace_path);

        if (reader.read_one_req(&req)) {
            std::cout << "Second request:\n";
            print_request(req);
        } else {
            std::cerr << "Failed to read second request\n";
        }

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << "\n";
        return 1;
    }

    return 0;
}