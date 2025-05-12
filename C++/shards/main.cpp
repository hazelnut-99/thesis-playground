#include <iostream>
#include <Shards/Shards.h>

int main() {
    auto shards = Shards::fixedSize(1000, 1024);  // total accesses, sketch size

    // Simulate a realistic trace
    for (int i = 0; i < 1000; ++i) {
        shards->feed("key" + std::to_string(i % 100));  // 100 unique keys
    }

    auto mrc = shards->mrc();
    for (const auto &entry : mrc) {
        std::cout << "Cache size: " << entry.first
                  << " → Miss ratio: " << entry.second << "\n";
    }
    
    shards->clear();

    delete shards;
    return 0;
}
